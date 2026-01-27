package com.callingagent.app.utils

import android.content.Context
import android.net.Uri
import android.util.Log
import org.apache.poi.ss.usermodel.*
import org.apache.poi.xssf.usermodel.XSSFWorkbook
import org.apache.poi.hssf.usermodel.HSSFWorkbook
import java.io.InputStream
import java.text.DecimalFormat

object ExcelReader {

    private const val TAG = "ExcelReader"

    /**
     * Read Excel file and return list of rows (each row is a list of cell values)
     */
    fun readExcelFile(context: Context, uri: Uri): List<List<String>> {
        val result = mutableListOf<List<String>>()

        try {
            val inputStream: InputStream? = context.contentResolver.openInputStream(uri)
            inputStream?.use { stream ->
                val workbook: Workbook = try {
                    XSSFWorkbook(stream) // .xlsx
                } catch (e: Exception) {
                    // Try .xls format
                    context.contentResolver.openInputStream(uri)?.use {
                        HSSFWorkbook(it)
                    } ?: throw e
                }

                val sheet: Sheet = workbook.getSheetAt(0)

                for (row in sheet) {
                    val rowData = mutableListOf<String>()

                    // Get the last cell number to handle empty cells
                    val lastCellNum = row.lastCellNum.toInt()

                    for (cellIndex in 0 until lastCellNum) {
                        val cell = row.getCell(cellIndex, Row.MissingCellPolicy.CREATE_NULL_AS_BLANK)
                        val cellValue = getCellValueAsString(cell)
                        rowData.add(cellValue)
                    }

                    // Only add non-empty rows
                    if (rowData.any { it.isNotBlank() }) {
                        result.add(rowData)
                        Log.d(TAG, "Row ${row.rowNum}: $rowData")
                    }
                }

                workbook.close()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error reading Excel file", e)
        }

        return result
    }

    /**
     * Convert cell value to string, handling different cell types
     * IMPORTANT: Phone numbers stored as numeric need special handling
     */
    private fun getCellValueAsString(cell: Cell?): String {
        if (cell == null) return ""

        return try {
            when (cell.cellType) {
                CellType.STRING -> cell.stringCellValue?.trim() ?: ""

                CellType.NUMERIC -> {
                    // Check if it's a phone number (no decimal, reasonable length)
                    val numericValue = cell.numericCellValue

                    // Use DecimalFormat to avoid scientific notation
                    // and preserve the full number
                    if (numericValue == numericValue.toLong().toDouble()) {
                        // It's a whole number (likely phone number)
                        val formatter = DecimalFormat("#")
                        formatter.maximumFractionDigits = 0
                        val formatted = formatter.format(numericValue)
                        Log.d(TAG, "Numeric cell converted: $numericValue -> '$formatted'")
                        formatted
                    } else {
                        // It has decimal places
                        numericValue.toString()
                    }
                }

                CellType.BOOLEAN -> cell.booleanCellValue.toString()

                CellType.FORMULA -> {
                    try {
                        // Try to get cached value first
                        when (cell.cachedFormulaResultType) {
                            CellType.STRING -> cell.stringCellValue?.trim() ?: ""
                            CellType.NUMERIC -> {
                                val numericValue = cell.numericCellValue
                                if (numericValue == numericValue.toLong().toDouble()) {
                                    DecimalFormat("#").format(numericValue)
                                } else {
                                    numericValue.toString()
                                }
                            }
                            else -> cell.toString()
                        }
                    } catch (e: Exception) {
                        cell.toString()
                    }
                }

                CellType.BLANK -> ""

                else -> cell.toString().trim()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error reading cell value", e)
            cell.toString()
        }
    }
}
