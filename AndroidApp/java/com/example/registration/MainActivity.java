package com.example.registration;

import android.content.Intent;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    EditText etUsername, etPassword, etConfirmPassword;
    Button btnOk;
    View progressPart1, progressPart2;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        etUsername = findViewById(R.id.etUsername);
        etPassword = findViewById(R.id.etPassword);
        etConfirmPassword = findViewById(R.id.etConfirmPassword);
        btnOk = findViewById(R.id.btnOk);
        progressPart1 = findViewById(R.id.progressPart1);
        progressPart2 = findViewById(R.id.progressPart2);

        // Initially set progress parts to gray
        progressPart1.setBackgroundColor(getResources().getColor(android.R.color.darker_gray));
        progressPart2.setBackgroundColor(getResources().getColor(android.R.color.darker_gray));

        // Add TextWatcher to validate password matching
        TextWatcher passwordWatcher = new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                validatePasswords();
            }

            @Override
            public void afterTextChanged(Editable s) {}
        };

        etPassword.addTextChangedListener(passwordWatcher);
        etConfirmPassword.addTextChangedListener(passwordWatcher);

        btnOk.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String username = etUsername.getText().toString().trim();
                String password = etPassword.getText().toString().trim();
                String confirmPassword = etConfirmPassword.getText().toString().trim();

                if (username.isEmpty()) {
                    Toast.makeText(MainActivity.this, "Please enter username", Toast.LENGTH_SHORT).show();
                    return;
                }

                if (password.isEmpty()) {
                    Toast.makeText(MainActivity.this, "Please enter password", Toast.LENGTH_SHORT).show();
                    return;
                }

                if (confirmPassword.isEmpty()) {
                    Toast.makeText(MainActivity.this, "Please confirm password", Toast.LENGTH_SHORT).show();
                    return;
                }

                if (!password.equals(confirmPassword)) {
                    Toast.makeText(MainActivity.this, "Passwords do not match!", Toast.LENGTH_SHORT).show();
                    return;
                }

                // Navigate to Page 2
                Intent intent = new Intent(MainActivity.this, Page2Activity.class);
                intent.putExtra("username", username);
                intent.putExtra("password", password);
                intent.putExtra("passwordMatch", true);
                startActivity(intent);
            }
        });
    }

    private void validatePasswords() {
        String password = etPassword.getText().toString().trim();
        String confirmPassword = etConfirmPassword.getText().toString().trim();

        if (!password.isEmpty() && !confirmPassword.isEmpty()) {
            if (password.equals(confirmPassword)) {
                // GREEN if passwords match
                progressPart1.setBackgroundColor(getResources().getColor(android.R.color.holo_green_dark));
            } else {
                // RED if passwords don't match
                progressPart1.setBackgroundColor(getResources().getColor(android.R.color.holo_red_dark));
            }
        } else {
            // GRAY if fields are empty
            progressPart1.setBackgroundColor(getResources().getColor(android.R.color.darker_gray));
        }
    }
}
