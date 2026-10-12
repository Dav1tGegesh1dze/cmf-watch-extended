package com.giftfile.watch2proreverse

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LifecycleEventEffect
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.giftfile.watch2proreverse.ble.*
import com.giftfile.watch2proreverse.ui.Strings

@Composable
fun App(model: WatchViewModel, onStartScan: () -> Unit = model::startScan, onOpenSettings: () -> Unit) {
    val state by model.state.collectAsStateWithLifecycle()
    var georgian by rememberSaveable { mutableStateOf(false) }
    val strings = remember(georgian) { Strings(georgian) }
    LifecycleEventEffect(Lifecycle.Event.ON_START) { model.refresh() }
    LifecycleEventEffect(Lifecycle.Event.ON_STOP) { model.stopScan() }
    val colors = if (isSystemInDarkTheme()) darkColorScheme(
        primary = Color(0xFFFF705F), background = Color(0xFF111112), surface = Color(0xFF1C1C1E)
    ) else lightColorScheme(primary = Color(0xFFAD3024), background = Color(0xFFF6F5F2), surface = Color.White)
    MaterialTheme(colorScheme = colors) {
        Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
            Box(Modifier.fillMaxSize().safeContentPadding(), contentAlignment = Alignment.TopCenter) {
                LazyColumn(
                    Modifier.widthIn(max = 760.dp).fillMaxWidth(),
                    contentPadding = PaddingValues(20.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                ) {
                    item {
                        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                            Text(strings.phase, Modifier.weight(1f), style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.primary)
                            TextButton(onClick = { georgian = !georgian }) { Text(if (georgian) "English" else "ქართული") }
                        }
                        Text(strings.title, style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Bold)
                        Text(strings.subtitle, style = MaterialTheme.typography.titleMedium)
                    }
                    item {
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                Text(if (state.isScanning) strings.scanning else strings.availability(state.availability),
                                    style = MaterialTheme.typography.titleMedium)
                                if (state.isScanning) LinearProgressIndicator(Modifier.fillMaxWidth())
                                Text(strings.duration, style = MaterialTheme.typography.bodySmall)
                                state.problem?.let { Text(strings.problem(it), color = MaterialTheme.colorScheme.error) }
                                Button(
                                    onClick = { if (state.isScanning) model.stopScan() else onStartScan() },
                                    enabled = state.isScanning || state.availability != BluetoothAvailability.UNSUPPORTED,
                                    modifier = Modifier.fillMaxWidth(),
                                ) { Text(if (state.isScanning) strings.stop else strings.start) }
                                if (state.availability !in listOf(BluetoothAvailability.READY, BluetoothAvailability.UNKNOWN)) {
                                    TextButton(onClick = onOpenSettings) { Text(strings.settings) }
                                    TextButton(onClick = model::refresh) { Text(strings.refresh) }
                                }
                            }
                        }
                    }
                    item { Text(strings.safety, style = MaterialTheme.typography.bodyMedium) }
                    item { Text("${strings.devices} · ${state.devices.size}", style = MaterialTheme.typography.titleLarge) }
                    if (state.devices.isEmpty()) item {
                        OutlinedCard(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text(strings.empty, fontWeight = FontWeight.SemiBold)
                                Text(strings.emptyHelp, style = MaterialTheme.typography.bodyMedium)
                            }
                        }
                    }
                    items(state.devices, key = { it.identifier }) { device ->
                        Card(Modifier.fillMaxWidth().animateItem()) {
                            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text(device.name ?: strings.unnamed, style = MaterialTheme.typography.titleMedium)
                                SelectionContainer {
                                    Text("${strings.identifier}: ${device.identifier}",
                                        style = MaterialTheme.typography.bodySmall, fontFamily = FontFamily.Monospace)
                                }
                                Text(device.rssi?.let { "$it dBm · RSSI" } ?: strings.unavailable,
                                    style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
                            }
                        }
                    }
                    item {
                        HorizontalDivider()
                        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                            Text(strings.diagnostics, Modifier.weight(1f), style = MaterialTheme.typography.titleLarge)
                            TextButton(onClick = model::clearDiagnostics) { Text(strings.clear) }
                        }
                        Text(strings.privacy, style = MaterialTheme.typography.bodySmall)
                    }
                    if (state.diagnostics.isEmpty()) item { Text(strings.noLogs) }
                    items(state.diagnostics.asReversed(), key = { "log-${it.sequence}" }) { entry ->
                        Text("#${entry.sequence}  ${strings.event(entry.event)}${entry.code?.let { " ($it)" } ?: ""}" +
                            (entry.availability?.let { ": ${strings.availability(it)}" } ?: ""),
                            style = MaterialTheme.typography.bodySmall)
                    }
                    item { Text(strings.georgianSample, style = MaterialTheme.typography.bodyMedium) }
                }
            }
        }
    }
}
