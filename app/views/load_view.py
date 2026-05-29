"""Selector de archivos GeoJSON con inspector de contenido.

Modulo que contiene la vista LoadView para seleccionar, eliminar y
previsualizar archivos GeoJSON antes del procesamiento.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from desktop_app.app import theme
from desktop_app.app.state import FileProcessingResult
from desktop_app.scripts.geojson_processor import inspect_geojson_file
from desktop_app.scripts.translator import t
from desktop_app.scripts import session_store


DELETE_COLUMN_WIDTH = 36
NAME_COLUMN_WIDTH = 190
PATH_COLUMN_MIN_WIDTH = 420
APPROX_CHAR_WIDTH = 7


class LoadView(tk.Frame):
    """Vista de seleccion de archivos GeoJSON con tabla e inspector."""

    def __init__(self, master, state):
        super().__init__(master, padx=24, pady=24, bg=theme.BG_ROOT)
        self.master = master
        self.state = state
        self.show_vertices = tk.BooleanVar(value=False)
        self.selected_file_indexes = set()
        self.last_selected_file_index = None
        self.file_row_widgets = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_actions()
        self._build_content()
        self._build_footer()
        self._refresh_files_table()
        self.after_idle(self._update_inspector_scrollbars)

    def _build_header(self):
        """Construye la cabecera con titulo y icono de perfil."""
        header = tk.Frame(self, bg=theme.BG_ROOT)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)

        title = tk.Label(
            header, text=t("load.title"), font=theme.FONT_TITLE_M,
            fg=theme.TEXT_TITLE, bg=theme.BG_ROOT,
        )
        title.grid(row=0, column=0, sticky="w")

        right_frame = tk.Frame(header, bg=theme.BG_ROOT)
        right_frame.grid(row=0, column=1, sticky="e")

        profile_label = tk.Label(
            right_frame, text="\U0001F464", font=("Segoe UI", 22),
            bg=theme.BG_ROOT, fg="#4A90D9", cursor="hand2",
        )
        profile_label.pack(side="left")
        profile_label.bind("<Button-1>", lambda _e: self.master.show_profile())

    def _build_actions(self):
        """Construye la barra de acciones (seleccionar, eliminar)."""
        actions = tk.Frame(self, bg=theme.BG_ROOT)
        actions.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        actions.grid_columnconfigure(2, weight=1)

        select_btn = theme.RoundedButton(
            actions, text=t("load.select_files"), command=self._select_files,
            bg=theme.BTN_PRIMARY, fg="#ffffff",
            activebackground=theme.BTN_PRIMARY_HOVER,
            font=theme.FONT_BODY, width=170, height=34,
        )
        select_btn.grid(row=0, column=0, padx=(0, 8))

        delete_btn = theme.RoundedButton(
            actions, text=t("load.delete_all"), command=self._delete_all_files,
            bg=theme.BTN_DANGER, fg="#ffffff",
            activebackground="#a11d1d", font=theme.FONT_BODY,
            width=130, height=34,
        )
        delete_btn.grid(row=0, column=1, padx=(0, 8))

    def _build_content(self):
        """Construye el contenido principal con tabla de archivos e inspector."""
        content = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg=theme.BG_ROOT)
        content.grid(row=2, column=0, sticky="nsew")

        files_frame = tk.LabelFrame(
            content, text=t("load.files_frame"),
            bg=theme.BG_PANEL, fg=theme.TEXT_TITLE, font=theme.FONT_SMALL_BOLD,
            relief="solid", borderwidth=1,
        )
        files_frame.grid_rowconfigure(1, weight=1)
        files_frame.grid_columnconfigure(0, weight=1)

        self.files_canvas = tk.Canvas(files_frame, highlightthickness=0, bg=theme.BG_PANEL)
        self.files_canvas.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))

        self.files_rows_frame = tk.Frame(self.files_canvas, bg=theme.BG_PANEL)
        self.files_canvas_window = self.files_canvas.create_window(
            (0, 0),
            window=self.files_rows_frame,
            anchor="nw",
        )
        self.files_rows_frame.bind("<Configure>", self._update_files_scroll_region)
        self._add_files_header()

        self.files_y_scroll = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_canvas.yview)
        self.files_y_scroll.grid(row=1, column=1, sticky="ns")
        self.files_x_scroll = ttk.Scrollbar(files_frame, orient=tk.HORIZONTAL, command=self.files_canvas.xview)
        self.files_x_scroll.grid(row=2, column=0, sticky="ew")
        self.files_canvas.configure(
            yscrollcommand=self.files_y_scroll.set,
            xscrollcommand=self.files_x_scroll.set,
        )
        self.files_canvas.bind("<Configure>", self._on_files_canvas_configure)

        content.add(files_frame, minsize=380)

        inspector_frame = tk.LabelFrame(
            content, text=t("load.inspector_frame"),
            bg=theme.BG_PANEL, fg=theme.TEXT_TITLE, font=theme.FONT_SMALL_BOLD,
            relief="solid", borderwidth=1,
        )
        inspector_frame.grid_rowconfigure(1, weight=1)
        inspector_frame.grid_columnconfigure(0, weight=1)

        inspector_actions = tk.Frame(inspector_frame, bg=theme.BG_PANEL)
        inspector_actions.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))
        inspector_actions.grid_columnconfigure(1, weight=1)

        theme.GreenCheckbox(
            inspector_actions,
            text=t("load.inspector_vertices"),
            variable=self.show_vertices,
            command=self._refresh_inspector,
            size=18,
        ).grid(row=0, column=0, sticky="w")

        self.inspector_text = tk.Text(
            inspector_frame, wrap="word", state="disabled",
            bg=theme.BG_CONTENT, fg=theme.TEXT_PRIMARY, font=theme.FONT_SMALL,
            insertbackground=theme.TEXT_PRIMARY, relief="flat", borderwidth=0,
        )
        self.inspector_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

        self.inspector_y_scroll = ttk.Scrollbar(
            inspector_frame, orient=tk.VERTICAL, command=self.inspector_text.yview,
        )
        self.inspector_y_scroll.grid(row=1, column=1, sticky="ns")
        self.inspector_x_scroll = ttk.Scrollbar(
            inspector_frame, orient=tk.HORIZONTAL, command=self.inspector_text.xview,
        )
        self.inspector_x_scroll.grid(row=2, column=0, sticky="ew")
        self.inspector_text.configure(
            yscrollcommand=self.inspector_y_scroll.set,
            xscrollcommand=self.inspector_x_scroll.set,
        )
        self.inspector_text.bind("<Configure>", lambda _event: self._update_inspector_scrollbars())

        content.add(inspector_frame, minsize=430)

    def _build_footer(self):
        """Construye el pie con el boton de procesar."""
        footer = tk.Frame(self, bg=theme.BG_ROOT)
        footer.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        footer.grid_columnconfigure(0, weight=1)

        process_btn = theme.RoundedButton(
            footer, text=t("load.process"), command=self._process_files,
            bg=theme.BTN_PRIMARY, fg="#ffffff",
            activebackground=theme.BTN_PRIMARY_HOVER,
            font=theme.FONT_BODY, width=150, height=36,
        )
        process_btn.grid(row=0, column=1, sticky="e")

    def _select_files(self):
        """Abre el dialogo de seleccion de archivos y agrega los nuevos."""
        filenames = filedialog.askopenfilenames(
            title=t("load.dialog_title"),
            filetypes=[("GeoJSON", "*.geojson"), ("JSON", "*.json"), (t("load.all_files"), "*.*")],
        )
        if not filenames:
            return

        existing = {path.resolve() for path in self.state.selected_files}
        added = 0
        for filename in filenames:
            path = Path(filename)
            resolved = path.resolve()
            if resolved not in existing:
                self.state.selected_files.append(path)
                existing.add(resolved)
                added += 1

        self._refresh_files_table()
        if added:
            self._select_last_file()

    def _delete_all_files(self):
        """Elimina todos los archivos seleccionados tras confirmacion."""
        if not self.state.selected_files:
            return
        if not theme.ask_yes_no(
            t("load.delete_all"),
            t("load.delete_confirm").format(count=len(self.state.selected_files)),
        ):
            return
        self.state.selected_files.clear()
        self.selected_file_indexes.clear()
        self.last_selected_file_index = None
        self._refresh_files_table()
        self._clear_inspector()

    def _delete_file_at(self, index):
        """Elimina un archivo de la lista por indice."""
        if 0 <= index < len(self.state.selected_files):
            del self.state.selected_files[index]
        self.selected_file_indexes = {
            selected if selected < index else selected - 1
            for selected in self.selected_file_indexes
            if selected != index and selected < len(self.state.selected_files) + 1
        }
        self.last_selected_file_index = None
        self._refresh_files_table()
        self._refresh_inspector()

    def _process_files(self):
        """Inicia el procesamiento de los archivos seleccionados."""
        if not self.state.selected_files:
            theme.show_warning(t("load.process"), t("load.empty_warning"))
            return

        self.state.reset_processing()
        for path in self.state.selected_files:
            self.state.set_file_result(FileProcessingResult(path=path))
        self.master.show_processing()

    def _refresh_files_table(self):
        """Refresca la tabla de archivos mostrando la lista actual."""
        for widget in self.files_rows_frame.winfo_children():
            widget.destroy()
        self.file_row_widgets = []
        self._add_files_header()

        self.selected_file_indexes = {
            index for index in self.selected_file_indexes if index < len(self.state.selected_files)
        }

        for index, path in enumerate(self.state.selected_files):
            self._add_file_row(index, path)

        self._update_file_delete_buttons()
        self.after_idle(self._update_files_scrollbars)
        self.after_idle(self._update_files_scroll_region)

    def _add_files_header(self):
        """Agrega la fila de cabecera de la tabla de archivos."""
        header = tk.Frame(self.files_rows_frame, bg=theme.ROW_HEADER_BG)
        header.grid(row=0, column=0, sticky="ew")
        self._configure_file_columns(header)

        tk.Label(header, text="", bg=theme.ROW_HEADER_BG).grid(row=0, column=0, sticky="nsew")
        tk.Label(
            header, text=t("load.col_name"), anchor="w", bg=theme.ROW_HEADER_BG, padx=6,
            fg=theme.TEXT_TITLE, font=theme.FONT_SMALL_BOLD,
        ).grid(row=0, column=1, sticky="nsew", padx=(1, 0))
        tk.Label(
            header, text=t("load.col_path"), anchor="w", bg=theme.ROW_HEADER_BG, padx=6,
            fg=theme.TEXT_TITLE, font=theme.FONT_SMALL_BOLD,
        ).grid(row=0, column=2, sticky="nsew", padx=(1, 0))

    def _add_file_row(self, index, path):
        """Agrega una fila a la tabla para un archivo."""
        selected = index in self.selected_file_indexes
        background = theme.ROW_SELECTED if selected else theme.ROW_NORMAL

        row = tk.Frame(self.files_rows_frame, bg=background)
        row.grid(row=index + 1, column=0, sticky="ew")
        self._configure_file_columns(row, path)

        delete_button = tk.Label(
            row,
            text="X",
            bg=background,
            fg=theme.BTN_DANGER,
            font=theme.FONT_SMALL_BOLD,
            cursor="hand2",
        )
        delete_button.grid(row=0, column=0, sticky="nsew")
        delete_button.bind("<Button-1>", lambda _event, file_index=index: self._delete_file_at(file_index))

        name_label = tk.Label(
            row, text=path.name, anchor="w", bg=background, padx=6,
            fg=theme.TEXT_PRIMARY, font=theme.FONT_BODY,
        )
        name_label.grid(row=0, column=1, sticky="nsew", padx=(1, 0))

        path_label = tk.Label(
            row, text=str(path), anchor="w", bg=background, padx=6,
            fg=theme.TEXT_SECONDARY, font=theme.FONT_SMALL,
        )
        path_label.grid(row=0, column=2, sticky="nsew", padx=(1, 0))

        for widget in (row, name_label, path_label):
            widget.bind("<Button-1>", lambda event, file_index=index: self._select_file_row(file_index, event))

        self.file_row_widgets.append((row, delete_button, name_label, path_label))

    def _select_last_file(self):
        """Selecciona el ultimo archivo de la lista."""
        if not self.state.selected_files:
            return
        last_index = len(self.state.selected_files) - 1
        self._set_selected_file_indexes({last_index})
        self.after_idle(lambda: self.files_canvas.yview_moveto(1.0))
        self._refresh_inspector()

    def _select_file_row(self, index, event=None):
        """Maneja la seleccion de fila con soporte para Ctrl y Shift."""
        if event and event.state & 0x0004:
            selected = set(self.selected_file_indexes)
            if index in selected:
                selected.remove(index)
            else:
                selected.add(index)
            self._set_selected_file_indexes(selected)
        elif event and event.state & 0x0001 and self.last_selected_file_index is not None:
            start = min(self.last_selected_file_index, index)
            end = max(self.last_selected_file_index, index)
            self._set_selected_file_indexes(set(range(start, end + 1)))
        else:
            self._set_selected_file_indexes({index})

        self.last_selected_file_index = index
        self._refresh_inspector()

    def _set_selected_file_indexes(self, indexes):
        """Establece los indices seleccionados y refresca la tabla."""
        self.selected_file_indexes = {
            index for index in indexes if 0 <= index < len(self.state.selected_files)
        }
        self._refresh_files_table()

    def _configure_file_columns(self, frame, path=None):
        """Configura el ancho de las columnas de la tabla."""
        path_width = PATH_COLUMN_MIN_WIDTH
        if path is not None:
            path_width = max(PATH_COLUMN_MIN_WIDTH, len(str(path)) * APPROX_CHAR_WIDTH + 16)

        frame.grid_columnconfigure(0, minsize=DELETE_COLUMN_WIDTH, weight=0)
        frame.grid_columnconfigure(1, minsize=NAME_COLUMN_WIDTH, weight=0)
        frame.grid_columnconfigure(2, minsize=path_width, weight=0)

    def _update_file_delete_buttons(self):
        """Actualiza el color de los botones de eliminar."""
        for _row, delete_button, _name_label, _path_label in self.file_row_widgets:
            delete_button.configure(fg=theme.BTN_DANGER)

    def _update_files_scrollbars(self):
        """Muestra u oculta las scrollbars segun el contenido."""
        if not self.state.selected_files:
            self.files_y_scroll.grid_remove()
            self.files_x_scroll.grid_remove()
            return

        self.files_canvas.update_idletasks()
        canvas_height = self.files_canvas.winfo_height()
        canvas_width = self.files_canvas.winfo_width()
        if canvas_height <= 1 or canvas_width <= 1:
            self.after_idle(self._update_files_scrollbars)
            return

        bbox = self.files_canvas.bbox("all")
        if not bbox:
            self.files_y_scroll.grid_remove()
            self.files_x_scroll.grid_remove()
            return

        content_height = bbox[3] - bbox[1]
        if content_height > canvas_height:
            self.files_y_scroll.grid()
        else:
            self.files_y_scroll.grid_remove()

        content_width = bbox[2] - bbox[0]
        if content_width > canvas_width:
            self.files_x_scroll.grid()
        else:
            self.files_x_scroll.grid_remove()

    def _on_files_canvas_configure(self, _event=None):
        """Callback al cambiar el tamano del canvas de archivos."""
        self.after_idle(self._update_files_scroll_region)
        self.after_idle(self._update_files_scrollbars)

    def _update_files_scroll_region(self, _event=None):
        """Actualiza la region de scroll del canvas de archivos."""
        if hasattr(self, "files_canvas"):
            self.files_canvas.configure(scrollregion=self.files_canvas.bbox("all"))

    def _refresh_inspector(self):
        """Refresca el inspector con el contenido del archivo seleccionado."""
        if not self.selected_file_indexes:
            self._clear_inspector()
            return

        index = min(self.selected_file_indexes)
        if index >= len(self.state.selected_files):
            self._clear_inspector()
            return

        text = inspect_geojson_file(
            self.state.selected_files[index],
            include_vertices=self.show_vertices.get(),
        )
        self._set_inspector_text(text)

    def _clear_inspector(self):
        """Limpia el inspector mostrando un mensaje por defecto."""
        self._set_inspector_text(t("load.inspector_placeholder"))

    def _set_inspector_text(self, text):
        """Establece el texto del inspector de forma segura."""
        self.inspector_text.configure(state="normal")
        self.inspector_text.delete("1.0", tk.END)
        self.inspector_text.insert(tk.END, text)
        self.inspector_text.configure(state="disabled")
        self.after_idle(self._update_inspector_scrollbars)

    def _update_inspector_scrollbars(self):
        """Muestra u oculta las scrollbars del inspector."""
        if not hasattr(self, "inspector_text"):
            return

        self.inspector_text.update_idletasks()

        if self.inspector_text.yview() == (0.0, 1.0):
            self.inspector_y_scroll.grid_remove()
        else:
            self.inspector_y_scroll.grid()

        if self.inspector_text.xview() == (0.0, 1.0):
            self.inspector_x_scroll.grid_remove()
        else:
            self.inspector_x_scroll.grid()
