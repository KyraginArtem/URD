class TemplateDatabaseService:
    @staticmethod
    def load_template_cells(self, template_id):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT TemplateCells.cell_id, cell_name, data, type, length, width, color, font, format, is_merged, merge_range
            FROM TemplateCells
            LEFT JOIN TemplateCellConfigurations ON TemplateCells.cell_id = TemplateCellConfigurations.cell_id
            WHERE template_id = %s
        """, (template_id,))
        cells = cursor.fetchall()
        cursor.close()

        cell_list = []
        for cell in cells:
            cell_list.append({
                "cell_name": cell["cell_name"],
                "value": cell["data"],
                "config": {
                    "type": cell.get("type"),
                    "length": cell.get("length"),
                    "width": cell.get("width"),
                    "color": cell.get("color"),
                    "font": cell.get("font"),
                    "format": cell.get("format"),
                    "merged": {
                        "is_merged": cell.get("is_merged", False),
                        "merge_range": cell.get("merge_range", None)
                    }
                }
            })

        return cell_list
