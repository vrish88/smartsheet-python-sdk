import pytest


@pytest.mark.usefixtures("smart_setup")
class TestRows:
    added_row = None
    copied_row_id = None
    sheet_primary_id = None
    added_row_with_dict = None

    def test_add_rows(self, smart_setup):
        smart = smart_setup['smart']
        row = smart.models.Row()
        row.to_top = True
        for col in smart_setup['sheet'].columns:
            if col.primary:
                TestRows.sheet_primary_id = col.id
                row.cells.append({
                    'column_id': col.id,
                    'value': 'Here is a new row'
                })
        action = smart_setup['sheet'].add_rows([row])
        added_row = action.result[0]
        TestRows.added_row = added_row
        assert isinstance(added_row, smart.models.row.Row)
        assert action.request_response.status_code == 200

    def test_add_row_with_dict(self, smart_setup):
        smart = smart_setup['smart']
        action = smart_setup['sheet'].add_rows({
            'cells': [{
                'column_id': TestRows.sheet_primary_id,
                'value': 'Row added with dict'
            }],
            'to_top': True
        })
        TestRows.added_row_with_dict = action.result[0]
        assert action.message == 'SUCCESS'

    def test_copy_rows(self, smart_setup):
        smart = smart_setup['smart']
        result = smart.Sheets.copy_rows(
            smart_setup['sheet'].id,
            smart.models.CopyOrMoveRowDirective({
                'row_ids': [TestRows.added_row.id],
                'to': smart.models.CopyOrMoveRowDestination({
                    'sheet_id': smart_setup['sheet_b'].id
                })
            })
        )
        TestRows.copied_row_id = result.row_mappings[0].to
        # should be CopyOrMoveRowResult
        assert isinstance(result, smart.models.copy_or_move_row_result.CopyOrMoveRowResult)
        assert isinstance(result.row_mappings[0], smart.models.row_mapping.RowMapping)

    def test_move_rows(self, smart_setup):
        smart = smart_setup['smart']
        result = smart.Sheets.move_rows(
            smart_setup['sheet_b'].id,
            smart.models.CopyOrMoveRowDirective({
                'row_ids': [smart_setup['sheet_b'].rows[0].id],
                'to': smart.models.CopyOrMoveRowDestination({
                    'sheet_id': smart_setup['sheet'].id
                })
            })
        )
        assert result.request_response.status_code == 200
        # should be CopyOrMoveRowResult
        assert isinstance(result, smart.models.copy_or_move_row_result.CopyOrMoveRowResult)

    def test_get_row(self, smart_setup):
        smart = smart_setup['smart']
        row = smart_setup['sheet_b'].get_row(TestRows.copied_row_id)
        assert row.request_response.status_code == 200

    def test_get_cell_history(self, smart_setup):
        smart = smart_setup['smart']
        row = smart_setup['sheet_b'].get_row(TestRows.copied_row_id)
        assert row.request_response.status_code == 200

        new_row = smart.models.Row()
        new_row.id = row.id
        new_row.cells = [smart.models.Cell]
        new_row.cells[0].column_id = row.cells[0].column_id
        new_row.cells[0].value = 'Now for something completely different.'
        changed_cell_id = row.cells[0].column_id
        action = smart.Sheets.update_rows(
            smart_setup['sheet_b'].id,
            [new_row]
        )
        assert action.message == 'SUCCESS'
        # now let's check the history
        action = smart.Cells.get_cell_history(
            smart_setup['sheet_b'].id,
            TestRows.copied_row_id,
            changed_cell_id
        )
        assert isinstance(action.result[0], smart.models.cell_history.CellHistory)

    def test_send_rows(self, smart_setup):
        smart = smart_setup['smart']
        sheetb = smart.Sheets.get_sheet(smart_setup['sheet_b'].id)
        ids = []
        column_ids = []
        for row in sheetb.rows:
            ids.append(row.id)
            for cell in row.cells:
                column_ids.append(cell.column_id)

        email = smart.models.MultiRowEmail()
        email.send_to = smart.models.Recipient({'email': 'john.doe@smartsheet.com'})
        email.row_ids = ids
        email.include_attachments = False
        email.include_discussions = False
        email.column_ids = list(set(column_ids))
        action = smart.Sheets.send_rows(
            smart_setup['sheet_b'].id,
            email
        )
        assert action.message == 'SUCCESS'

    def test_delete_rows(self, smart_setup):
        smart = smart_setup['smart']
        action = smart_setup['sheet'].delete_rows([TestRows.added_row.id])
        assert action.message == 'SUCCESS'

    def test_update_rows(self, smart_setup):
        smart = smart_setup['smart']

        row = smart_setup['sheet'].get_row(TestRows.added_row_with_dict.id)

        new_row = smart.models.Row()
        new_row.id = row.id
        new_row.cells = [smart.models.Cell]
        new_row.cells[0].column_id = row.cells[0].column_id
        new_row.cells[0].value = smart.models.ExplicitNull()
        new_row.to_bottom = True
        new_row.to_top = False
        action = smart.Sheets.update_rows(
            smart_setup['sheet'].id,
            [new_row]
        )
        assert action.message == 'SUCCESS'

    def test_update_rows_alternate_approach(self, smart_setup):
        smart = smart_setup['smart']
        row = smart_setup['sheet'].get_row(TestRows.added_row_with_dict.id)
        cell = row.get_column(TestRows.sheet_primary_id)
        cell.value = 'sneaky, sis!'
        new_row = smart.models.Row()
        new_row.id = row.id
        new_row.set_column(TestRows.sheet_primary_id, cell)
        action = smart.Sheets.update_rows(
            smart_setup['sheet'].id,
            [new_row]
        )
        assert action.message == 'SUCCESS'

    def test_add_rows_partial_success(self, smart_setup):
        smart = smart_setup['smart']

        new_row_a = smart.models.Row()
        new_row_a.cells = [smart.models.Cell]
        new_row_b = smart.models.Row()
        new_row_b.cells = [smart.models.Cell]
        for col in smart_setup['sheet'].columns:
            if col.primary:
                new_row_a.cells[0].column_id = col.id
                new_row_a.cells[0].value = 'this is a good row'
        new_row_b.cells[0].column_id = 123
        new_row_b.cells[0].value = 'this is a bad row'

        action = smart.Sheets.add_rows_with_partial_success(smart_setup['sheet'].id, [new_row_a,new_row_b])
        assert action.message == 'PARTIAL_SUCCESS'
        assert isinstance(action, smart.models.BulkItemResult)

    def test_update_rows_partial_success(self, smart_setup):
        smart = smart_setup['smart']

        row = smart_setup['sheet'].get_row(TestRows.added_row_with_dict.id)
        new_row_a = smart.models.Row()
        new_row_b = smart.models.Row()
        new_row_a.id = row.id
        new_row_b.id = 123
        new_row_a.cells = [smart.models.Cell]
        new_row_b.cells = [smart.models.Cell]
        for col in smart_setup['sheet'].columns:
            if col.primary:
                new_row_a.cells[0].column_id = col.id
                new_row_a.cells[0].value = 'this is a good row'
                new_row_b.cells[0].column_id = col.id
                new_row_b.cells[0].value = 'this is a bad row'

        action = smart.Sheets.update_rows_with_partial_success(smart_setup['sheet'].id, [new_row_a,new_row_b])
        assert action.message == 'PARTIAL_SUCCESS'
        assert isinstance(action, smart.models.BulkItemResult)
