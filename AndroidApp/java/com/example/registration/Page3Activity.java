package com.example.registration;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

public class Page3Activity extends AppCompatActivity {

    TextView tvUsername, tvPassword, tvAge, tvGender;
    Button btnBack;
    View progressPart1, progressPart2;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_page3);

        tvUsername = findViewById(R.id.tvUsername);
        tvPassword = findViewById(R.id.tvPassword);
        tvAge = findViewById(R.id.tvAge);
        tvGender = findViewById(R.id.tvGender);
        btnBack = findViewById(R.id.btnBack);
        progressPart1 = findViewById(R.id.progressPart1);
        progressPart2 = findViewById(R.id.progressPart2);

        // Get data from previous pages
        Intent intent = getIntent();
        String username = intent.getStringExtra("username");
        String password = intent.getStringExtra("password");
        String age = intent.getStringExtra("age");
        String gender = intent.getStringExtra("gender");
        boolean passwordMatch = intent.getBooleanExtra("passwordMatch", false);

        // Display data (hide password with ****)
        tvUsername.setText("Username: " + username);
        tvPassword.setText("Password: " + maskPassword(password));
        tvAge.setText("Age: " + age);
        tvGender.setText("Gender: " + gender);

        // Set progress bar - both parts filled
        if (passwordMatch) {
            progressPart1.setBackgroundColor(getResources().getColor(android.R.color.holo_green_dark));
        } else {
            progressPart1.setBackgroundColor(getResources().getColor(android.R.color.holo_red_dark));
        }
        progressPart2.setBackgroundColor(getResources().getColor(android.R.color.holo_blue_dark));

        btnBack.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish(); // Go back to Page 2
            }
        });
    }

    private String maskPassword(String password) {
        StringBuilder masked = new StringBuilder();
        for (int i = 0; i < password.length(); i++) {
            masked.append("*");
        }
        return masked.toString();
    }
}
