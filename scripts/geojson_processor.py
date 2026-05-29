"""Motor de procesamiento de GeoJSON con consulta a Catastro.

Modulo que contiene la logica para validar, procesar e insertar datos
de archivos GeoJSON en la base de datos, incluyendo consulta al Catastro
y construccion de referencias catastrales.
"""

import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from desktop_app.app.state import FileProcessingResult, ProcessingSummary, STATUS_DONE, STATUS_ERROR
from desktop_app.scripts.supabase_client import SupabaseError
from desktop_app.scripts.translator import t

try:
    from stdnum.es import referenciacatastral
except Exception:
    referenciacatastral = None


CADASTRAL_ALPHABET = "ABCDEFGHIJKLMN" + "\u00d1" + "OPQRSTUVWXYZ0123456789"
CADASTRAL_CONTROL_CHARS = "MQWERTYUIOPASDFGHJKLBZX"
CADASTRAL_WEIGHTS = (13, 15, 12, 5, 4, 17, 9, 21, 3, 7, 1)


def process_geojson_files(file_paths, supabase_client=None, log_callback=None, progress_callback=None):
    """Procesa multiples archivos GeoJSON y devuelve un resumen."""
    summary = ProcessingSummary()

    for file_path in file_paths:
        result = process_single_geojson_file(
            file_path, supabase_client=supabase_client, log_callback=log_callback,
            progress_callback=progress_callback,
        )
        _update_summary(summary, result)

    return summary


def process_single_geojson_file(file_path, supabase_client=None, log_callback=None, progress_callback=None):
    """Procesa un archivo GeoJSON individual: valida, consulta Catastro e inserta."""
    path = Path(file_path)
    result = FileProcessingResult(path=path)

    def log(message):
        result.logs.append(message)
        _log(log_callback, message)

    log(f"## {t('log.info_general')}")
    log(f"{t('log.file')}: {path.name}")
    log(f"{t('log.path')}: {path}")
    log(t("log.validating"))

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return _fail(result, t("log.file_not_found").format(path=path))
    except json.JSONDecodeError as exc:
        return _fail(result, t("log.json_invalid").format(lineno=exc.lineno, colno=exc.colno, msg=exc.msg))
    except Exception as exc:
        return _fail(result, t("log.file_read_error").format(error=exc))

    root_type = data.get("type")
    log(f"{t('log.root_type')}: {root_type or t('log.no_type')}")
    if root_type != "FeatureCollection":
        log(t("log.expected_feature_collection"))

    features = data.get("features")
    if not isinstance(features, list):
        return _fail(result, t("log.no_features_list"))

    log(f"{t('log.features_found')}: {len(features)}")
    if not features:
        return _fail(result, t("log.no_features"))

    parcel_numbers = set()
    parcel_refs = set()

    for index, feature in enumerate(features, start=1):
        log("")
        log(f"## {t('log.feature')} {index}/{len(features)}")

        if not isinstance(feature, dict):
            return _fail(result, t("log.feature_not_json").format(index=index))

        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}

        feature_id = feature.get("id", "")
        parcel = str(properties.get("parcela", "")).strip()
        polygon = str(properties.get("poligono", "")).strip()
        enclosure = str(properties.get("recinto", "")).strip()
        sigpac_use = str(properties.get("uso_sigpac", "")).strip()
        geometry_type = geometry.get("type", "")
        vertices = _count_vertices(geometry.get("coordinates"))

        log(f"### {t('log.data_recinto')}")
        log(f"{t('log.id_sigpac')}: {feature_id or t('log.no_id_fallback')}")
        log(f"{t('log.parcel')}: {parcel or t('log.no_parcel_fallback')}")
        log(f"{t('log.polygon')}: {polygon or t('log.no_polygon_fallback')}")
        log(f"{t('log.enclosure')}: {enclosure or t('log.no_enclosure_fallback')}")
        log(f"{t('log.use_sigpac')}: {sigpac_use or t('log.no_use_fallback')}")

        log(f"### {t('log.geometry')}")
        log(f"{t('log.geom_type')}: {geometry_type or t('log.no_geometry_fallback')}")
        log(f"{t('log.vertices')}: {vertices}")

        if not feature_id:
            return _fail(result, t("log.no_id").format(index=index))
        if not geometry_type:
            return _fail(result, t("log.no_geom").format(index=index))
        if not vertices:
            return _fail(result, t("log.no_coords").format(index=index))

        if parcel:
            parcel_numbers.add(parcel)

        log(f"### {t('log.catastro_query')}")
        log(t("log.basic_valid"))
        log(t("log.calculating_point"))
        lon, lat, point_source = _representative_point_for_log(geometry, log)
        log(f"{t('log.point_used')}: lon={_format_coord(lon)}, lat={_format_coord(lat)} ({point_source})")

        ref_catastral, sheet_code = _fetch_catastro_data(lon, lat, log)
        if len(_normalize_cadastral_ref(ref_catastral)) != 20:
            ref_catastral, sheet_code = _build_sigpac_cadastral_fallback(properties, log)

        if ref_catastral:
            log(f"{t('log.ref_final')}: {ref_catastral}")
            log(f"{t('log.sheet_final')}: {sheet_code or t('log.no_sheet_code')}")
        else:
            log(t("log.ref_not_found"))

        recinto_payload = {
            "id_recinto_sigpac": feature_id,
            "ref_catastral": ref_catastral,
            "num_poligono": polygon,
            "num_recinto": enclosure,
            "uso_sigpac": sigpac_use or "OV",
            "geom": geometry,
        }
        parcela_payload = {
            "ref_catastral": ref_catastral,
            "codigo_hoja": sheet_code,
            "num_parcela": parcel,
        }

        result.recintos.append(recinto_payload)
        if ref_catastral and ref_catastral not in parcel_refs:
            result.parcelas.append(parcela_payload)
            parcel_refs.add(ref_catastral)

        log(f"### {t('log.payload_ready')}")
        log(f"  {t('log.enclosure')} -> {feature_id}")
        if ref_catastral:
            log(f"  {t('log.parcel')} -> {ref_catastral}")

        if progress_callback:
            progress_callback(result)

    result.status = STATUS_DONE
    result.enclosures_detected = len(result.recintos)
    result.parcels_detected = len(result.parcelas)

    log("")
    log(f"## {t('log.result')}")
    log(f"{t('log.parcels_detected_log')}: {result.enclosures_detected}")
    log(f"{t('log.parcels_inserted_log')}: {result.parcels_detected}")

    if supabase_client is None:
        log(t("log.insertion_omitted"))
        return result

    log("")
    log(f"## {t('log.insertion_db')}")

    log(f"### {t('log.insertion_parcels')}")
    for parcela in result.parcelas:
        ref = parcela.get("ref_catastral", "")
        try:
            inserted = supabase_client.insert_parcela(parcela)
            if inserted:
                result.parcels_inserted += 1
                log(f"{t('log.inserted')}: {ref}")
            else:
                msg = f"{t('log.already_exists')}: {ref}"
                result.insertion_errors.append(msg)
                log(f"@@ERR@@ {t('log.error_prefix')}: {msg}")
        except SupabaseError as exc:
            msg = t("log.insert_parcel_error").format(ref=ref, error=exc)
            result.insertion_errors.append(msg)
            log(f"@@ERR@@ {t('log.error_prefix')}: {msg}")
        if progress_callback:
            progress_callback(result)

    log(f"### {t('log.insertion_enclosures')}")
    for recinto in result.recintos:
        rid = recinto.get("id_recinto_sigpac", "")
        try:
            inserted = supabase_client.insert_recinto(recinto)
            if inserted:
                result.enclosures_inserted += 1
                log(f"{t('log.inserted_enc')}: {rid}")
            else:
                msg = f"{t('log.already_exists')}: {rid}"
                result.insertion_errors.append(msg)
                log(f"@@ERR@@ {t('log.error_prefix')}: {msg}")
        except SupabaseError as exc:
            msg = t("log.insert_enclosure_error").format(rid=rid, error=exc)
            result.insertion_errors.append(msg)
            log(f"@@ERR@@ {t('log.error_prefix')}: {msg}")
        if progress_callback:
            progress_callback(result)

    log("")
    log(f"### {t('log.insertion_summary')}")
    log(f"{t('log.parcels_inserted_count')}: {result.parcels_inserted}")
    log(f"{t('log.enclosures_inserted_count')}: {result.enclosures_inserted}")
    if result.insertion_errors:
        log(f"{t('log.errors_count')}: {len(result.insertion_errors)}")

    return result


def build_summary_from_results(results):
    """Construye un resumen global a partir de multiples resultados."""
    summary = ProcessingSummary()
    for result in results:
        _update_summary(summary, result)
    return summary


def _update_summary(summary, result):
    if result.status == STATUS_DONE:
        summary.files_processed += 1
        summary.enclosures_detected += result.enclosures_detected
        summary.parcels_detected += result.parcels_detected
        summary.parcels_inserted += result.parcels_inserted
        summary.enclosures_inserted += result.enclosures_inserted
        summary.errors.extend(result.feature_errors)
        summary.errors.extend(result.insertion_errors)
    elif result.status == STATUS_ERROR:
        summary.errors.append(result.error or t("log.processing_error").format(name=result.path.name))
        summary.errors.extend(result.feature_errors)


def _fail(result, message):
    result.status = STATUS_ERROR
    result.error = message
    result.feature_errors.append(message)
    result.logs.append(f"@@ERR@@ {t('log.error_prefix')}: {message}")
    return result


def _log(callback, message):
    if callback is not None:
        callback(message)


def _xml_text(tree, field_name):
    for element in tree.iter():
        local_name = element.tag.split("}", 1)[-1].lower()
        if local_name == field_name.lower() and element.text:
            return element.text.strip().upper()
    return ""


def _normalize_cadastral_ref(value):
    return "".join(str(value).split()).upper()


def _is_valid_cadastral_ref(ref_catastral):
    ref_catastral = _normalize_cadastral_ref(ref_catastral)
    if len(ref_catastral) != 20:
        return False
    if referenciacatastral is None:
        return _calc_check_digits_local(ref_catastral[:18]) == ref_catastral[18:]
    try:
        return referenciacatastral.is_valid(ref_catastral)
    except AttributeError:
        try:
            referenciacatastral.validate(ref_catastral)
            return True
        except Exception:
            return False
    except Exception:
        return False


def _calculate_check_digits(ref_18, log):
    ref_18 = _normalize_cadastral_ref(ref_18)
    if len(ref_18) != 18:
        return ""
    if referenciacatastral is None:
        return _calc_check_digits_local(ref_18)
    try:
        return referenciacatastral.calc_check_digits(ref_18)
    except Exception as exc:
        log(f"  {t('log.warn_check_digit').format(ref=ref_18, error=exc)}")
        return ""


def _check_digit_local(number):
    total = 0
    for weight, char in zip(CADASTRAL_WEIGHTS, number):
        value = int(char) if char.isdigit() else CADASTRAL_ALPHABET.find(char) + 1
        total += weight * value
    return CADASTRAL_CONTROL_CHARS[total % 23]


def _calc_check_digits_local(ref_18):
    ref_18 = _normalize_cadastral_ref(ref_18)
    return (
        _check_digit_local(ref_18[0:7] + ref_18[14:18])
        + _check_digit_local(ref_18[7:14] + ref_18[14:18])
    )


def _build_cadastral_ref(tree, log):
    """Construye la referencia catastral completa a partir del XML del Catastro."""
    # Extraer componentes del XML
    pc1 = _xml_text(tree, "pc1")
    pc2 = _xml_text(tree, "pc2")
    car = _xml_text(tree, "car")
    cc1 = _xml_text(tree, "cc1")
    cc2 = _xml_text(tree, "cc2")

    log(f"  {t('log.xml_data_read')}")
    log(f"    pc1={pc1 or 'None'}, pc2={pc2 or 'None'}, car={car or 'None'}, cc1={cc1 or 'None'}, cc2={cc2 or 'None'}")

    if not pc1 or not pc2:
        return "", "", t("log.origin_no_data")

    parcel_14 = _normalize_cadastral_ref(pc1 + pc2)
    sheet_code = pc1[:6] if len(pc1) >= 6 else pc1

    # Si hay CAR y digitos de control, intentar referencia oficial
    if car and cc1 and cc2:
        official_ref = _normalize_cadastral_ref(parcel_14 + car + cc1 + cc2)
        if _is_valid_cadastral_ref(official_ref):
            return official_ref, sheet_code, t("log.origin_official")
        if referenciacatastral is None and len(official_ref) == 20:
            log(f"  {t('log.warn_stdnum_unavailable')}")
            return official_ref, sheet_code, t("log.origin_official_unvalidated")
        log(f"  {t('log.warn_invalid_ref').format(ref=official_ref)}")

    # Construir referencia con CAR o 0000 y calcular digitos de control
    ref_18 = _normalize_cadastral_ref(parcel_14 + (car if car else "0000"))
    check_digits = _calculate_check_digits(ref_18, log)
    if check_digits:
        origin = t("log.origin_calculated_car") if car else t("log.origin_calculated_0000")
        return ref_18 + check_digits, sheet_code, origin

    return parcel_14, sheet_code, t("log.origin_partial")


def _fetch_catastro_data(lon, lat, log):
    """Consulta la API del Catastro para obtener la referencia catastral."""
    log(f"  {t('log.querying_catastro')}")
    if lon is None or lat is None:
        log(f"  {t('log.no_valid_point')}")
        return "", ""

    url = (
        "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/"
        "OVCCoordenadas.asmx/Consulta_RCCOOR"
        f"?SRS=EPSG:4326&Coordenada_X={lon}&Coordenada_Y={lat}"
    )
    log(f"  {t('log.query_url')}: {url}")

    try:
        response = urllib.request.urlopen(url, timeout=10)
        xml_data = response.read()
        log(f"  {t('log.response_received').format(size=len(xml_data))}")
        tree = ET.fromstring(xml_data)

        ref_catastral, sheet_code, origin = _build_cadastral_ref(tree, log)
        if origin == "oficial":
            log(f"  {t('log.ref_official_read')}")
        elif origin == "oficial_sin_validar":
            log(f"  {t('log.ref_complete_pending')}")
        elif origin == "calculada_con_car":
            log(f"  {t('log.ref_completed_car')}")
        elif origin == "calculada_con_0000":
            log(f"  {t('log.ref_rebuilt_0000')}")
        elif origin == "parcial":
            log(f"  {t('log.ref_partial')}")
        else:
            log(f"  {t('log.catastro_no_data')}")

        return ref_catastral, sheet_code
    except Exception as exc:
        log(f"  {t('log.catastro_error').format(error=exc)}")
        return "", ""


def _build_sigpac_cadastral_fallback(properties, log):
    """Construye una referencia catastral de respaldo usando datos SIGPAC."""
    log(f"{t('log.sigpac_fallback_start')}")

    province = _digits_or_empty(properties.get("provincia"), 2)
    municipality = _digits_or_empty(properties.get("municipio"), 3)
    polygon = _digits_or_empty(properties.get("poligono"), 3)
    parcel = _digits_or_empty(properties.get("parcela"), 5)
    sector = _sector_from_sigpac(properties.get("agregado"), properties.get("zona"), log)

    log(f"  {t('log.sigpac_fields')}")
    log(f"    {t('log.sigpac_province')}={province or 'None'}")
    log(f"    {t('log.sigpac_municipality')}={municipality or 'None'}")
    log(f"    {t('log.sigpac_sector')}={sector or 'None'}")
    log(f"    {t('log.sigpac_polygon')}={polygon or 'None'}")
    log(f"    {t('log.sigpac_parcel')}={parcel or 'None'}")

    if not all((province, municipality, sector, polygon, parcel)):
        log(f"  {t('log.sigpac_missing_fields')}")
        return "", ""

    parcel_14 = province + municipality + sector + polygon + parcel
    ref_18 = parcel_14 + "0000"
    check_digits = _calculate_check_digits(ref_18, log)
    if not check_digits:
        log(f"  {t('log.sigpac_check_digit_fail')}")
        return "", ""

    ref_catastral = ref_18 + check_digits
    sheet_code = parcel_14[:6]

    if _is_valid_cadastral_ref(ref_catastral):
        log(f"  {t('log.sigpac_ref_rebuilt').format(ref=ref_catastral)}")
    else:
        log(f"  {t('log.sigpac_fallback_warning').format(ref=ref_catastral)}")

    log(f"  {t('log.sigpac_note')}")
    return ref_catastral, sheet_code


def _digits_or_empty(value, width):
    text = str(value).strip()
    if not text:
        return ""
    if "." in text:
        text = text.split(".", 1)[0]
    if not text.isdigit():
        return ""
    return text.zfill(width)[-width:]


def _sector_from_sigpac(aggregate, zone, log):
    aggregate_text = _integer_text_or_empty(aggregate)
    zone_text = _integer_text_or_empty(zone)
    sector_value = aggregate_text or zone_text
    if sector_value in ("", "0"):
        log(f"  {t('log.sector_fallback_zero')}")
        return "A"

    try:
        index = int(sector_value)
    except ValueError:
        return ""

    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if 0 <= index < len(letters):
        sector = letters[index]
        log(f"  {t('log.sector_fallback').format(value=sector_value, sector=sector)}")
        return sector

    return ""


def _integer_text_or_empty(value):
    text = str(value).strip()
    if not text:
        return ""
    if "." in text:
        text = text.split(".", 1)[0]
    return text if text.isdigit() else ""


def _ring_area(ring):
    area = 0
    for index in range(len(ring) - 1):
        x1, y1 = ring[index][:2]
        x2, y2 = ring[index + 1][:2]
        area += x1 * y2 - x2 * y1
    return area / 2


def _ring_centroid(ring):
    area = _ring_area(ring)
    if area == 0:
        lon = sum(point[0] for point in ring) / len(ring)
        lat = sum(point[1] for point in ring) / len(ring)
        return lon, lat

    factor_lon = 0
    factor_lat = 0
    for index in range(len(ring) - 1):
        x1, y1 = ring[index][:2]
        x2, y2 = ring[index + 1][:2]
        factor = x1 * y2 - x2 * y1
        factor_lon += (x1 + x2) * factor
        factor_lat += (y1 + y2) * factor

    return factor_lon / (6 * area), factor_lat / (6 * area)


def _point_in_ring(point, ring):
    """Determina si un punto esta dentro de un anillo (algoritmo ray casting)."""
    x, y = point
    inside = False
    previous_index = len(ring) - 1
    for index in range(len(ring)):
        xi, yi = ring[index][:2]
        xj, yj = ring[previous_index][:2]
        crosses = (yi > y) != (yj > y)
        if crosses:
            intersection_x = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < intersection_x:
                inside = not inside
        previous_index = index
    return inside


def _point_in_polygon(point, polygon):
    if not polygon:
        return False
    outer_ring = polygon[0]
    if not _point_in_ring(point, outer_ring):
        return False
    return not any(_point_in_ring(point, hole) for hole in polygon[1:])


def _interior_point_for_polygon(polygon, log):
    outer_ring = polygon[0]
    centroid = _ring_centroid(outer_ring)
    log(f"  {t('log.centroid_calculated').format(lon=_format_coord(centroid[0]), lat=_format_coord(centroid[1]))}")
    if _point_in_polygon(centroid, polygon):
        log(f"  {t('log.centroid_inside')}")
        return centroid, "centroide interior"

    min_lon = min(point[0] for point in outer_ring)
    max_lon = max(point[0] for point in outer_ring)
    min_lat = min(point[1] for point in outer_ring)
    max_lat = max(point[1] for point in outer_ring)
    log(f"  {t('log.centroid_outside')}")

    # Buscar punto interior mediante rejilla creciente
    for divisions in (4, 8, 16):
        for ix in range(1, divisions):
            for iy in range(1, divisions):
                candidate = (
                    min_lon + (max_lon - min_lon) * ix / divisions,
                    min_lat + (max_lat - min_lat) * iy / divisions,
                )
                if _point_in_polygon(candidate, polygon):
                    log(f"  {t('log.grid_point_found').format(n=divisions)}")
                    return candidate, f"{t('log.source_grid').format(n=divisions)}"

    fallback = outer_ring[0][:2]
    log(f"  {t('log.no_interior_point')}")
    return fallback, t("log.source_first_vertex")


def _representative_point_for_log(geometry, log):
    try:
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates", [])

        if geometry_type == "Polygon" and coordinates:
            point, source = _interior_point_for_polygon(coordinates, log)
            return point[0], point[1], source

        if geometry_type == "MultiPolygon" and coordinates:
            largest_polygon = max(coordinates, key=lambda polygon: abs(_ring_area(polygon[0])) if polygon else 0)
            log(f"  {t('log.multipolygon_detected')}")
            point, source = _interior_point_for_polygon(largest_polygon, log)
            return point[0], point[1], f"{t('log.source_largest_area')}, {source}"
    except Exception as exc:
        log(f"  {t('log.repr_point_error').format(error=exc)}")

    return None, None, t("log.source_not_calculated")


def _format_coord(value):
    if value is None:
        return "None"
    return f"{value:.8f}"


def _preview_coordinates(coordinates, max_chars=600):
    return _truncate_text(json.dumps(coordinates, ensure_ascii=False), max_chars)


def _preview_value(value, max_chars=800):
    if isinstance(value, dict) and "coordinates" in value:
        geometry_type = value.get("type", t("log.no_type"))
        coordinates = _preview_coordinates(value.get("coordinates"), max_chars=500)
        return _truncate_text(f"type={geometry_type}, coordinates={coordinates}", max_chars)
    if isinstance(value, (dict, list)):
        return _truncate_text(json.dumps(value, ensure_ascii=False), max_chars)
    return str(value)


def _truncate_text(text, max_chars):
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + " ..."


def inspect_geojson_file(file_path, include_vertices=False):
    """Inspecciona un archivo GeoJSON y devuelve un resumen legible."""
    path = Path(file_path)

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as exc:
        return t("inspector.read_error").format(name=path.name, error=exc)

    lines = [
        f"{t('inspector.file')}: {path.name}",
        f"{t('inspector.path')}: {path}",
        "",
        f"{t('inspector.root_type')}: {data.get('type', t('inspector.unknown'))}",
    ]

    features = data.get("features")
    if not isinstance(features, list):
        lines.append("")
        lines.append(t("inspector.no_features"))
        return "\n".join(lines)

    lines.append(f"{t('inspector.features')}: {len(features)}")
    lines.append("")

    for index, feature in enumerate(features, start=1):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        lines.append(f"{t('inspector.feature')} {index}")
        lines.append(f"  id: {feature.get('id', '')}")
        lines.append(f"  {t('inspector.feature_type')}: {feature.get('type', '')}")
        lines.append(f"  {t('inspector.geom_type')}: {geometry.get('type', '')}")
        lines.append(f"  {t('inspector.vertices')}: {_count_vertices(geometry.get('coordinates'))}")
        lines.append(f"  {t('inspector.properties')}:")

        if isinstance(properties, dict) and properties:
            for key, value in properties.items():
                lines.append(f"    {key}: {value}")
        else:
            lines.append(f"    {t('inspector.no_properties')}")

        if include_vertices:
            lines.append(f"  {t('inspector.coordinates')}:")
            coordinates = json.dumps(geometry.get("coordinates", []), ensure_ascii=False, indent=4)
            lines.extend(f"    {line}" for line in coordinates.splitlines())
        else:
            lines.append(f"  {t('inspector.coordinates')}: {t('inspector.hidden')}")

        lines.append("")

    text = "\n".join(lines)
    max_chars = 60000
    if len(text) > max_chars:
        return text[:max_chars] + f"\n\n{t('inspector.truncated')}"
    return text


def _count_vertices(value):
    if not isinstance(value, list):
        return 0

    if value and all(isinstance(item, (int, float)) for item in value[:2]):
        return 1

    return sum(_count_vertices(item) for item in value)
