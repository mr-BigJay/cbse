package com.ardm.agent.commands

sealed class LocalResult {
    data class Ok(val message: String) : LocalResult()
    data class Rejected(val message: String) : LocalResult()
    data class Failed(val message: String) : LocalResult()
}
