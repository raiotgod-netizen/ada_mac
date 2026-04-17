"""
Creates Formulario_Inscripcion.xlsm using win32com.
Creates: Sheets (Apoyo, Datos, Menu), UserForm1, VBA Modules, Buttons.
"""
import os
import sys
import win32com.client
from pathlib import Path

ADA_DIR = r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2'
OUTPUT = os.path.join(ADA_DIR, 'Formulario_Inscripcion.xlsm')

def create_excel_with_vba():
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    wb = excel.Workbooks.Add()

    # --- Hoja Apoyo ---
    ws_apoyo = wb.Sheets(1)
    ws_apoyo.Name = "Apoyo"
    ws_apoyo.Range("A1").Value = "IDCurso"
    ws_apoyo.Range("B1").Value = "NombreCurso"
    ws_apoyo.Range("C1").Value = "Precio"
    ws_apoyo.Range("A1:C1").Font.Bold = True

    cursos = [
        ("CUR001", "Introduccion a la Programacion", 15000),
        ("CUR002", "Python Avanzado", 25000),
        ("CUR003", "Excel con Macros", 18000),
        ("CUR004", "Analisis de Datos con Excel", 22000),
        ("CUR005", "Power BI Fundamentals", 30000),
        ("CUR006", "Machine Learning Basics", 45000),
        ("CUR007", "Base de Datos SQL", 20000),
        ("CUR008", "Presentaciones Ejecutivas", 12000),
    ]
    for i, (cod, nom, pre) in enumerate(cursos, 2):
        ws_apoyo.Cells(i, 1).Value = cod
        ws_apoyo.Cells(i, 2).Value = nom
        ws_apoyo.Cells(i, 3).Value = pre
        ws_apoyo.Cells(i, 3).NumberFormat = '"$"#,##0.00'

    ws_apoyo.Columns("A").ColumnWidth = 12
    ws_apoyo.Columns("B").ColumnWidth = 35
    ws_apoyo.Columns("C").ColumnWidth = 15

    # --- Hoja Datos ---
    ws_datos = wb.Sheets.Add()
    ws_datos.Name = "Datos"
    headers = ["Nombre y Apellido", "ID Curso", "Precio", "Fecha Inscripcion"]
    for col, h in enumerate(headers, 1):
        c = ws_datos.Cells(1, col)
        c.Value = h
        c.Font.Bold = True
    ws_datos.Columns("A").ColumnWidth = 30
    ws_datos.Columns("B").ColumnWidth = 12
    ws_datos.Columns("C").ColumnWidth = 15
    ws_datos.Columns("D").ColumnWidth = 22

    # --- Hoja Menu ---
    ws_menu = wb.Sheets.Add()
    ws_menu.Name = "Menu"
    ws_menu.Range("A1").Value = "FORMULARIO DE INSCRIPCION"
    ws_menu.Range("A1").Font.Bold = True
    ws_menu.Range("A1").Font.Size = 16
    ws_menu.Range("A3").Value = "Haga clic en el boton para abrir el formulario de inscripcion"
    ws_menu.Range("A5").Value = "Nota: habilite macros al abrir el archivo"
    ws_menu.Range("A5").Font.Italic = True
    ws_menu.Range("A5").Font.Color = 8421504

    # Button to show form
    btn = ws_menu.Buttons.Add(100, 100, 200, 40)
    btn.Text = "Abrir Formulario"
    btn.OnAction = "MostrarFormulario"

    # --- VBA Module ---
    vba_module_code = """Sub MostrarFormulario()
    UserForm1.Show
End Sub

Sub INSCRIPCION()
    Dim wsDatos As Worksheet
    Dim wsApoyo As Worksheet
    Dim lastRow As Long
    Dim cursoId As String
    Dim precio As Variant
    Dim nombre As String
    
    Set wsDatos = ThisWorkbook.Sheets("Datos")
    Set wsApoyo = ThisWorkbook.Sheets("Apoyo")
    
    nombre = UserForm1.txtNombre.Value
    cursoId = UserForm1.cmbCurso.Value
    
    If nombre = "" Then
        MsgBox "Ingrese nombre y apellido.", vbExclamation
        Exit Sub
    End If
    
    If cursoId = "" Then
        MsgBox "Seleccione un curso.", vbExclamation
        Exit Sub
    End If
    
    On Error Resume Next
    precio = Application.WorksheetFunction.VLookup(cursoId, wsApoyo.Range("A:C"), 3, False)
    On Error GoTo 0
    
    lastRow = wsDatos.Cells(wsDatos.Rows.Count, 1).End(xlUp).Row + 1
    wsDatos.Cells(lastRow, 1).Value = nombre
    wsDatos.Cells(lastRow, 2).Value = cursoId
    wsDatos.Cells(lastRow, 3).Value = precio
    wsDatos.Cells(lastRow, 4).Value = Now
    
    MsgBox "Inscripcion exitosa: " & nombre & " - " & Format(precio, "$#,##0.00"), vbInformation
    Call BORRAR
End Sub

Sub BORRAR()
    On Error Resume Next
    UserForm1.txtNombre.Value = ""
    UserForm1.cmbCurso.Value = ""
    UserForm1.lblPrecio.Caption = ""
    On Error GoTo 0
End Sub

Sub CARGAR_CURSOS()
    Dim wsApoyo As Worksheet
    Dim lastRow As Long
    Dim i As Long
    
    Set wsApoyo = ThisWorkbook.Sheets("Apoyo")
    lastRow = wsApoyo.Cells(wsApoyo.Rows.Count, 1).End(xlUp).Row
    
    UserForm1.cmbCurso.Clear
    For i = 2 To lastRow
        UserForm1.cmbCurso.AddItem wsApoyo.Cells(i, 1).Value
    Next i
End Sub
"""

    # Add VBA module
    try:
        vba_proj = wb.VBProject
        vba_mod = vba_proj.VBComponents.Add(1)  # 1 = vbext_ct_StdModule
        vba_mod.CodeModule.AddFromString(vba_module_code)
    except Exception as e:
        print(f"Warning: Could not add VBA module: {e}")
        print("VBA code will be provided in separate .bas file")

    # Save as .xlsm
    try:
        wb.SaveAs(OUTPUT, FileFormat=52)  # 52 = xlOpenXMLWorkbookMacroEnabled
        print(f"Archivo guardado: {OUTPUT}")
    except Exception as e:
        print(f"Error al guardar: {e}")
        # Try alternative path
        alt_path = os.path.join(ADA_DIR, 'Formulario_Inscripcion_v2.xlsm')
        wb.SaveAs(alt_path, FileFormat=52)
        print(f"Guardado en: {alt_path}")

    wb.Close(False)
    excel.Quit()
    print("Proceso completado.")

if __name__ == '__main__':
    create_excel_with_vba()
