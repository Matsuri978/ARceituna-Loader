"""Vista de procesamiento en tiempo real con log.

Modulo que contiene la vista ProcessingView que muestra el progreso
del procesamiento de archivos GeoJSON, con tabla de archivos y log en vivo.
"""

import tkinter as tk
from tkinter import ttk

from desktop_app.app import theme
from desktop_app.app.state import STATUS_DONE, STATUS_ERROR, STATUS_PENDING, STATUS_PROCESSING
from desktop_app.scripts.geojson_processor import build_summary_from_results, process_single_geojson_file
from desktop_app.scripts.translator import t


STATUS_LABELS = {
    STATUS_PENDING: "◌",
    STATUS_PROCESSING: "⟳",
    STATUS_DONE: "✓",
    STATUS_ERROR: "✕",
}


class ProcessingView(tk.Frame):
    """Vista de procesamiento con tabla de archivos y log en tiempo real."""

    def __init__(self, master, state):
        super().__init__(master, padx=24, pady=24, bg=theme.BG_ROOT)
        self.master = master
        self.state = state
        self.processing_files = list(state.selected_files)
        self.current_index = 0
        self.processing_finished = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_summary()
        self._build_content()
        self._build_footer()
        self._refresh_files_table()
        self._select_file(0)

        self.after(250, self._process_next_file)

    def _build_header(self):
        """Construye la cabecera con titulo y subtitulo."""
        header = tk.Frame(self, bg=theme.BG_ROOT)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header, text=t("processing.title"), font=theme.FONT_TITLE_M,
            fg=theme.TEXT_TITLE, bg=theme.BG_ROOT,
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            header, text=t("processing.subtitle"),
            fg=theme.TEXT_SECONDARY, bg=theme.BG_ROOT,
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    def _build_summary(self):
        """Construye el panel de metricas de resumen."""
        frame = tk.LabelFrame(
            self, text=t("processing.summary_title"), padx=12, pady=10,
            bg=theme.BG_PANEL, fg=theme.TEXT_TITLE, font=theme.FONT_SMALL_BOLD,
            relief="solid", borderwidth=1,
        )
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        self._summary_labels = {}
        metrics = [
            ("files_processed", t("processing.files")),
            ("parcels_detected", t("processing.parcels_detected")),
            ("parcels_inserted", t("processing.parcels_inserted")),
            ("enclosures_detected", t("processing.enclosures_detected")),
            ("enclosures_inserted", t("processing.enclosures_inserted")),
            ("errors", t("processing.errors")),
        ]

        for col, (key, label_text) in enumerate(metrics):
            frame.grid_columnconfigure(col, weight=1)

            if col > 0:
                sep = tk.Frame(frame, bg=theme.BORDER, width=1)
                sep.grid(row=0, column=col, rowspan=2, sticky="ns", padx=6, pady=2)

            cell = tk.Frame(frame, bg=theme.BG_PANEL)
            cell.grid(row=0, column=col, rowspan=2 if col == 0 else 1, sticky="nsew")
            cell.grid_columnconfigure(0, weight=1)

            val_label = tk.Label(
                cell, text="0", font=("Segoe UI", 18, "bold"),
                fg=theme.TEXT_TITLE, bg=theme.BG_PANEL, anchor="center",
            )
            val_label.grid(row=0, column=0, sticky="ew")
            tk.Label(
                cell, text=label_text, font=theme.FONT_SMALL,
                fg=theme.TEXT_SECONDARY, bg=theme.BG_PANEL, anchor="center",
            ).grid(row=1, column=0, sticky="ew")
            self._summary_labels[key] = val_label

    def _refresh_summary(self, current_result=None):
        """Actualiza las metricas del resumen con los datos actuales."""
        summary = self.state.summary
        values = {
            "files_processed": summary.files_processed,
            "parcels_detected": summary.parcels_detected + (current_result.parcels_detected if current_result else 0),
            "parcels_inserted": summary.parcels_inserted + (current_result.parcels_inserted if current_result else 0),
            "enclosures_detected": summary.enclosures_detected + (current_result.enclosures_detected if current_result else 0),
            "enclosures_inserted": summary.enclosures_inserted + (current_result.enclosures_inserted if current_result else 0),
            "errors": len(summary.errors) + len(current_result.insertion_errors) if current_result else len(summary.errors),
        }
        for key, label in self._summary_labels.items():
            label.configure(text=str(values.get(key, 0)))

    def _build_content(self):
        """Construye el contenido con tabla de archivos y panel de log."""
        content = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg=theme.BG_ROOT)
        content.grid(row=2, column=0, sticky="nsew")

        files_frame = tk.LabelFrame(
            content, text=t("processing.files_frame"),
            bg=theme.BG_PANEL, fg=theme.TEXT_TITLE, font=theme.FONT_SMALL_BOLD,
            relief="solid", borderwidth=1,
        )
        files_frame.grid_rowconfigure(0, weight=1)
        files_frame.grid_columnconfigure(0, weight=1)

        self.files_table = ttk.Treeview(
            files_frame,
            columns=("name", "status"),
            show="headings",
            selectmode="browse",
        )
        self.files_table.heading("name", text=t("processing.files"))
        self.files_table.heading("status", text=t("processing.status"))
        self.files_table.column("name", width=300, anchor="w")
        self.files_table.column("status", width=80, anchor="center", stretch=False)
        self.files_table.tag_configure(STATUS_PENDING, foreground=theme.STATUS_PENDING_FG)
        self.files_table.tag_configure(STATUS_PROCESSING, foreground=theme.STATUS_PROCESSING_FG)
        self.files_table.tag_configure(STATUS_DONE, foreground=theme.STATUS_DONE_FG)
        self.files_table.tag_configure(STATUS_ERROR, foreground=theme.STATUS_ERROR_FG)
        self.files_table.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.files_y_scroll = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_table.yview)
        self.files_y_scroll.grid(row=0, column=1, sticky="ns")
        self.files_x_scroll = ttk.Scrollbar(files_frame, orient=tk.HORIZONTAL, command=self.files_table.xview)
        self.files_x_scroll.grid(row=1, column=0, sticky="ew")
        self.files_table.configure(
            yscrollcommand=self.files_y_scroll.set,
            xscrollcommand=self.files_x_scroll.set,
        )
        self.files_table.bind("<Configure>", self._update_files_scrollbars)
        self.files_table.bind("<<TreeviewSelect>>", self._on_file_selected)

        content.add(files_frame, minsize=330)

        log_frame = tk.LabelFrame(
            content, text=t("processing.log_frame"),
            bg=theme.BG_PANEL, fg=theme.TEXT_TITLE, font=theme.FONT_SMALL_BOLD,
            relief="solid", borderwidth=1,
        )
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_frame, wrap="word", state="disabled",
            bg=theme.BG_CONTENT, fg=theme.TEXT_PRIMARY, font=theme.FONT_SMALL,
            insertbackground=theme.TEXT_PRIMARY, relief="flat", borderwidth=0,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self._configure_log_tags()

        self.log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=self.log_scroll.set)
        self.log_text.bind("<Configure>", self._update_log_scrollbar)

        content.add(log_frame, minsize=430)

    def _build_footer(self):
        """Construye el pie con el boton de volver."""
        footer = tk.Frame(self, bg=theme.BG_ROOT)
        footer.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        footer.grid_columnconfigure(0, weight=1)

        back_btn = theme.RoundedButton(
            footer, text=t("processing.back"), command=self.master.show_loader,
            bg=theme.BTN_PRIMARY, fg="#ffffff",
            activebackground=theme.BTN_PRIMARY_HOVER, font=theme.FONT_BODY,
            width=120, height=34,
        )
        back_btn.grid(row=0, column=1, padx=(0, 8))

    def _process_next_file(self):
        """Procesa el siguiente archivo de la cola."""
        if self.current_index >= len(self.processing_files):
            self.processing_finished = True
            results = [self.state.file_results[str(path)] for path in self.processing_files]
            self.state.summary = build_summary_from_results(results)
            has_errors = any(
                r.status == STATUS_ERROR or r.insertion_errors
                for r in results
            )
            if not has_errors:
                self.state.selected_files.clear()
            self._refresh_summary()
            return

        path = self.processing_files[self.current_index]
        result = self.state.file_results[str(path)]
        result.status = STATUS_PROCESSING
        result.logs.append(t("processing.queued"))
        result.logs.append(t("processing.processing_now"))
        self.state.set_file_result(result)
        self._refresh_files_table()
        self._select_file(self.current_index)
        self.update_idletasks()

        processed_result = process_single_geojson_file(
            path, supabase_client=self.master.supabase_client, log_callback=self._append_live_log,
            progress_callback=lambda r: self._refresh_summary(r),
        )
        self.state.set_file_result(processed_result)
        self.state.log_lines.extend(processed_result.logs)

        summary = self.state.summary
        summary.files_processed += 1
        summary.parcels_detected += processed_result.parcels_detected
        summary.enclosures_detected += processed_result.enclosures_detected
        summary.parcels_inserted += processed_result.parcels_inserted
        summary.enclosures_inserted += processed_result.enclosures_inserted
        summary.errors.extend(processed_result.insertion_errors)
        self._refresh_summary()

        self._refresh_files_table()
        self._select_file(self.current_index)

        self.current_index += 1
        self.after(350, self._process_next_file)

    def _refresh_files_table(self):
        """Refresca la tabla de archivos con sus estados."""
        selected = self.files_table.selection()
        self.files_table.delete(*self.files_table.get_children())

        for index, path in enumerate(self.processing_files):
            result = self.state.file_results.get(str(path))
            status = result.status if result else STATUS_PENDING
            self.files_table.insert(
                "",
                tk.END,
                iid=str(index),
                values=(path.name, STATUS_LABELS.get(status, "")),
                tags=(status,),
            )

        for item_id in selected:
            if self.files_table.exists(item_id):
                self.files_table.selection_set(item_id)
        self.after_idle(self._update_files_scrollbars)

    def _select_file(self, index):
        """Selecciona un archivo en la tabla y muestra su log."""
        if not self.processing_files:
            self._set_log_text(t("processing.no_files"))
            return

        index = min(index, len(self.processing_files) - 1)
        item_id = str(index)
        if self.files_table.exists(item_id):
            self.files_table.selection_set(item_id)
            self.files_table.focus(item_id)
            self.files_table.see(item_id)
        self._show_log_for_index(index)

    def _on_file_selected(self, _event=None):
        """Callback al seleccionar un archivo en la tabla."""
        selected = self.files_table.selection()
        if not selected:
            return
        self._show_log_for_index(int(selected[0]))

    def _show_log_for_index(self, index):
        """Muestra el log del archivo en el indice dado."""
        path = self.processing_files[index]
        result = self.state.file_results.get(str(path))
        if result is None or not result.logs:
            text = t("processing.pending")
            self._set_log_text(text)
        else:
            self._set_log_lines(result.logs)

    def _set_log_text(self, text):
        """Establece el texto del log de forma segura."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert(tk.END, text)
        self.log_text.configure(state="disabled")
        self.log_text.see(tk.END)
        self.after_idle(self._update_log_scrollbar)

    def _configure_log_tags(self):
        """Configura los estilos de texto para el log (errores, secciones)."""
        self.log_text.tag_configure("error", foreground=theme.TEXT_ERROR)
        self.log_text.tag_configure(
            "section_header",
            font=("Segoe UI", 10, "bold"),
            foreground=theme.TEXT_TITLE,
            background=theme.ROW_HEADER_BG,
            lmargin1=4, lmargin2=4, rmargin=4,
            spacing3=4,
        )
        self.log_text.tag_configure(
            "subsection_header",
            font=("Segoe UI", 9, "bold"),
            foreground=theme.TEXT_TITLE,
            lmargin1=8,
            spacing3=2,
        )
        self.log_text.tag_configure(
            "indent",
            foreground=theme.TEXT_SECONDARY,
            lmargin1=16,
        )

    def _set_log_lines(self, lines):
        """Muestra multiples lineas de log con formato."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        for line in lines:
            if line.startswith("@@ERR@@ "):
                self.log_text.insert(tk.END, line[8:] + "\n", "error")
            elif line.startswith("## "):
                self.log_text.insert(tk.END, line[3:] + "\n", "section_header")
            elif line.startswith("### "):
                self.log_text.insert(tk.END, line[4:] + "\n", "subsection_header")
            elif line.startswith("  "):
                self.log_text.insert(tk.END, line + "\n", "indent")
            else:
                self.log_text.insert(tk.END, line + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see(tk.END)
        self.after_idle(self._update_log_scrollbar)

    def _append_live_log(self, line):
        """Agrega una linea al log en tiempo real durante el procesamiento."""
        selected = self.files_table.selection()
        if selected and int(selected[0]) != self.current_index:
            return

        self.log_text.configure(state="normal")
        if self.log_text.index("end-1c") != "1.0":
            self.log_text.insert(tk.END, "\n")
        if line.startswith("@@ERR@@ "):
            self.log_text.insert(tk.END, line[8:], "error")
        elif line.startswith("## "):
            self.log_text.insert(tk.END, line[3:], "section_header")
        elif line.startswith("### "):
            self.log_text.insert(tk.END, line[4:], "subsection_header")
        elif line.startswith("  "):
            self.log_text.insert(tk.END, line, "indent")
        else:
            self.log_text.insert(tk.END, line)
        self.log_text.configure(state="disabled")
        self.log_text.see(tk.END)
        self.update_idletasks()
        self.after_idle(self._update_log_scrollbar)

    def _update_files_scrollbars(self, _event=None):
        """Muestra u oculta las scrollbars de la tabla de archivos."""
        self.files_table.update_idletasks()
        children = self.files_table.get_children()
        if not children:
            self.files_y_scroll.grid_remove()
            self.files_x_scroll.grid_remove()
            return

        tree_height = self.files_table.winfo_height()
        tree_width = self.files_table.winfo_width()
        if tree_height <= 1 or tree_width <= 1:
            return

        row_height = 28
        content_height = len(children) * row_height
        if content_height > tree_height:
            self.files_y_scroll.grid()
        else:
            self.files_y_scroll.grid_remove()

        total_width = sum(self.files_table.column(c, "width") for c in self.files_table["columns"])
        if total_width > tree_width:
            self.files_x_scroll.grid()
        else:
            self.files_x_scroll.grid_remove()

    def _update_log_scrollbar(self, _event=None):
        """Muestra u oculta la scrollbar del log."""
        if self.log_text.yview() == (0.0, 1.0):
            self.log_scroll.grid_remove()
        else:
            self.log_scroll.grid()
