package com.giftfile.watch2proreverse

import androidx.compose.ui.window.ComposeUIViewController
import androidx.lifecycle.viewmodel.compose.viewModel
import com.giftfile.watch2proreverse.ble.IosBleController
import com.giftfile.watch2proreverse.ble.WatchRepository
import com.giftfile.watch2proreverse.ble.WatchViewModel
import platform.Foundation.NSURL
import platform.UIKit.UIApplication
import platform.UIKit.UIApplicationOpenSettingsURLString

fun MainViewController() = ComposeUIViewController {
    val model = viewModel { WatchViewModel(WatchRepository(IosBleController())) }
    App(model, onOpenSettings = {
        NSURL.URLWithString(UIApplicationOpenSettingsURLString)?.let {
            UIApplication.sharedApplication.openURL(it, emptyMap<Any?, Any>(), null)
        }
    })
}
