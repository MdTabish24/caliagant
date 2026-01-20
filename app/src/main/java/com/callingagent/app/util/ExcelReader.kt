package com.callingagent.app.util

import android.content.Context
import android.net.Uri
import org.apache.poi.ss.usermodel.CellType
import org.apache.poi.ss.usermodel.WorkbookFactory
import java.io.InputStream

object ExcelReader {

    fun readPhoneNumbers(context: Context, uri: Uri): List<String> {
        val phoneNumbers = mutableListOf<String>()
        
        try {
            val inputStream: InputStream? = context.contentResolver.openInputStream(uri)
            inputStream?.use { stream ->
                val workbook = WorkbookFactory.create(stream)
                val sheet = workbook.getSheetAt(0) // First sheet
                
                // Iterate through all rows
                for (rowIndex in 0..sheet.lastRowNum) {
                    val row = sheet.getRow(rowIndex) ?: continue
                    
                    // Get first column (index 0) - always phone number
                    val cell = row.getCell(0) ?: continue
                    
                    val phoneNumber = when (cell.cellType) {
                        CellType.STRING -> cell.stringCellValue.trim()
                        CellType.NUMERIC -> cell.numericCellValue.toLong().toString()
                        else -> continue
                    }
                    
                    // Clean and validate phone number
                    val cleanNumber = cleanPhoneNumber(phoneNumber)
                    if (cleanNumber.isNotEmpty() && isValidPhoneNumber(cleanNumber)) {
                        phoneNumbers.add(cleanNumber)
                    }
                }
                
                workbook.close()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        
        return phoneNumbers
    }

    private fun cleanPhoneNumber(number: String): String {
        // Remove all non-digit characters except +
        return number.replace(Regex("[^0-9+]"), "")
    }

    private fun isValidPhoneNumber(number: String): Boolean {
        // Basic validation - at least 10 digits
        val digitsOnly = number.replace("+", "")
        return digitsOnly.length >= 10
    }
}
