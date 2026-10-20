      startParentPcAutoReconnect()
    }

    override fun onPause() {
        stopParentPcAutoReconnect()
        super.onPause()
    }

