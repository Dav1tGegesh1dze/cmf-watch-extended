package com.giftfile.watch2proreverse

interface Platform {
    val name: String
}

expect fun getPlatform(): Platform