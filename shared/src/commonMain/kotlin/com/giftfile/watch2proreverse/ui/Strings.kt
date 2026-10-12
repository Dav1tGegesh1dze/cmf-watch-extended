package com.giftfile.watch2proreverse.ui

import com.giftfile.watch2proreverse.ble.*

/** Explicit in-app language selection also makes Georgian rendering easy to validate. */
class Strings(val georgian: Boolean) {
    private fun text(en: String, ka: String) = if (georgian) ka else en
    val title = "CMF Watch Extended"
    val subtitle = text("Discover nearby devices", "ახლომდებარე მოწყობილობები")
    val phase = text("PHASE 01 · DISCOVERY", "ეტაპი 01 · აღმოჩენა")
    val safety = text("Discovery only. No pairing or watch commands. Your watch may not advertise while connected to the official CMF app. Keep your current pairing.", "მხოლოდ აღმოჩენა. დაწყვილებისა და საათისთვის ბრძანებების გაგზავნის გარეშე. ოფიციალურ CMF აპთან დაკავშირებული საათი შესაძლოა არ გამოჩნდეს. შეინარჩუნეთ არსებული დაწყვილება.")
    val start = text("Start scan", "სკანირების დაწყება")
    val stop = text("Stop scan", "სკანირების შეწყვეტა")
    val scanning = text("Scanning nearby…", "მიმდინარეობს სკანირება…")
    val duration = text("15-second scans · foreground only", "15-წამიანი სკანირება · მხოლოდ გახსნილ აპში")
    val devices = text("Nearby devices", "ახლომდებარე მოწყობილობები")
    val empty = text("No devices yet", "მოწყობილობები ჯერ არ არის")
    val emptyHelp = text("Start a scan with Bluetooth enabled. Absence from this list does not mean your watch is unsupported.", "ჩართეთ Bluetooth და დაიწყეთ სკანირება. სიაში არყოფნა არ ნიშნავს, რომ თქვენი საათი მხარდაჭერილი არ არის.")
    val unnamed = text("Unnamed device", "უსახელო მოწყობილობა")
    val identifier = text("Identifier", "იდენტიფიკატორი")
    val unavailable = text("RSSI unavailable", "RSSI მიუწვდომელია")
    val diagnostics = text("Diagnostics", "დიაგნოსტიკა")
    val clear = text("Clear", "გასუფთავება")
    val noLogs = text("No diagnostic events", "დიაგნოსტიკური ჩანაწერები არ არის")
    val privacy = text("Logs stay in memory and contain no device identifiers or notification content. Up to 200 devices and 80 events are retained.", "ჟურნალი ინახება მხოლოდ მეხსიერებაში, მოწყობილობის იდენტიფიკატორებისა და შეტყობინებების შიგთავსის გარეშე. ინახება მაქსიმუმ 200 მოწყობილობა და 80 ჩანაწერი.")
    val settings = text("Open settings", "პარამეტრების გახსნა")
    val refresh = text("Check again", "ხელახლა შემოწმება")
    val georgianSample = text("Phone font preview: გამარჯობა · საქართველო · როგორ ხარ? · შეტყობინება", "ტელეფონის შრიფტის ნიმუში: გამარჯობა · საქართველო · როგორ ხარ? · შეტყობინება")
    fun availability(value: BluetoothAvailability) = when(value) {
        BluetoothAvailability.UNKNOWN -> text("Bluetooth: checking on scan", "Bluetooth: შემოწმდება სკანირებისას")
        BluetoothAvailability.READY -> text("Bluetooth ready", "Bluetooth მზად არის")
        BluetoothAvailability.PERMISSION_REQUIRED -> text("Bluetooth permission required. Tap Start scan to continue.", "საჭიროა Bluetooth-ის ნებართვა. გასაგრძელებლად დაიწყეთ სკანირება.")
        BluetoothAvailability.PERMISSION_DENIED -> text("Permission denied. Allow Bluetooth access in app settings.", "ნებართვა უარყოფილია. დაუშვით Bluetooth-ზე წვდომა აპის პარამეტრებში.")
        BluetoothAvailability.POWERED_OFF -> text("Bluetooth is off. Enable it in system settings.", "Bluetooth გამორთულია. ჩართეთ სისტემის პარამეტრებში.")
        BluetoothAvailability.UNSUPPORTED -> text("BLE is not available on this device.", "ამ მოწყობილობაზე BLE მიუწვდომელია.")
        BluetoothAvailability.LOCATION_DISABLED -> text("This Android version also requires Location services enabled for scanning.", "Android-ის ამ ვერსიაზე სკანირებისთვის საჭიროა მდებარეობის სერვისის ჩართვაც.")
    }
    fun problem(value: ScanProblem) = when (value) {
        ScanProblem.PERMISSION_DENIED -> text("Bluetooth permission was not granted.", "Bluetooth-ის ნებართვა არ გაიცა.")
        ScanProblem.START_FAILED -> text("Scan failed. Wait briefly, check Bluetooth, then try again.", "სკანირება ვერ შესრულდა. მოიცადეთ, შეამოწმეთ Bluetooth და სცადეთ ხელახლა.")
        ScanProblem.SCANNER_UNAVAILABLE -> text("The Bluetooth scanner is unavailable.", "Bluetooth სკანერი მიუწვდომელია.")
        ScanProblem.STOP_FAILED -> text("The system could not confirm scan cleanup. Check Bluetooth permissions.", "სისტემამ სკანირების დასრულება ვერ დაადასტურა. შეამოწმეთ Bluetooth-ის ნებართვები.")
    }
    fun event(value: DiagnosticEvent) = when(value) {
        DiagnosticEvent.AVAILABILITY_CHANGED -> text("Bluetooth availability changed", "Bluetooth-ის ხელმისაწვდომობა შეიცვალა")
        DiagnosticEvent.SCAN_STARTED -> text("Scan started", "სკანირება დაიწყო")
        DiagnosticEvent.SCAN_STOPPED -> text("Scan stopped", "სკანირება შეწყდა")
        DiagnosticEvent.SCAN_TIMED_OUT -> text("15-second scan completed", "15-წამიანი სკანირება დასრულდა")
        DiagnosticEvent.SCAN_FAILED -> text("Scan error", "სკანირების შეცდომა")
        DiagnosticEvent.PERMISSION_DENIED -> text("Permission denied", "ნებართვა უარყოფილია")
    }
}
