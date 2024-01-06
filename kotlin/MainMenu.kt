package com.lanlords.vertimeter

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity


class MainMenuActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_home)
        val btnmulai = findViewById<Button>(R.id.btn_mulai)
        btnmulai.setOnClickListener {
            val intent = Intent(
                this@MainMenuActivity,
                MainActivity::class.java
            )
            startActivity(intent)
        }
    }
}

