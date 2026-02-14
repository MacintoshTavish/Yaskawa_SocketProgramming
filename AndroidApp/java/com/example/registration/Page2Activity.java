package com.example.registration;

import android.content.Intent;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class Page2Activity extends AppCompatActivity {

    EditText etAge;
    RadioGroup rgGender;
    Button btnBack, btnOk;
    View progressPart1, progressPart2;

    String username, password;
    boolean passwordMatch;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_page2);

        etAge = findViewById(R.id.etAge);
        rgGender = findViewById(R.id.rgGender);
        btnBack = findViewById(R.id.btnBack);
        btnOk = findViewById(R.id.btnOk);
        progressPart1 = findViewById(R.id.progressPart1);
        progressPart2 = findViewById(R.id.progressPart2);

        // Get data from Page 1
        Intent intent = getIntent();
        username = intent.getStringExtra("username");
        password = intent.getStringExtra("password");
        passwordMatch = intent.getBooleanExtra("passwordMatch", false);

        // Set progress part 1 based on Page 1 validation
        if (passwordMatch) {
            progressPart1.setBackgroundColor(getResources().getColor(android.R.color.holo_green_dark));
        } else {
            progressPart1.setBackgroundColor(getResources().getColor(android.R.color.holo_red_dark));
        }

        // Initially gray for part 2
        progressPart2.setBackgroundColor(getResources().getColor(android.R.color.darker_gray));

        // Monitor age and gender input
        etAge.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                updateProgressPart2();
            }

            @Override
            public void afterTextChanged(Editable s) {}
        });

        rgGender.setOnCheckedChangeListener(new RadioGroup.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(RadioGroup group, int checkedId) {
                updateProgressPart2();
            }
        });

        btnBack.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish(); // Go back to Page 1
            }
        });

        btnOk.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String age = etAge.getText().toString().trim();
                int selectedGenderId = rgGender.getCheckedRadioButtonId();

                if (age.isEmpty()) {
                    Toast.makeText(Page2Activity.this, "Please enter age", Toast.LENGTH_SHORT).show();
                    return;
                }

                if (selectedGenderId == -1) {
                    Toast.makeText(Page2Activity.this, "Please select gender", Toast.LENGTH_SHORT).show();
                    return;
                }

                RadioButton selectedGender = findViewById(selectedGenderId);
                String gender = selectedGender.getText().toString();

                // Navigate to Page 3
                Intent intent = new Intent(Page2Activity.this, Page3Activity.class);
                intent.putExtra("username", username);
                intent.putExtra("password", password);
                intent.putExtra("age", age);
                intent.putExtra("gender", gender);
                intent.putExtra("passwordMatch", passwordMatch);
                startActivity(intent);
            }
        });
    }

    private void updateProgressPart2() {
        String age = etAge.getText().toString().trim();
        int selectedGenderId = rgGender.getCheckedRadioButtonId();

        if (!age.isEmpty() && selectedGenderId != -1) {
            // BLUE if both age and gender are filled
            progressPart2.setBackgroundColor(getResources().getColor(android.R.color.holo_blue_dark));
        } else {
            // GRAY if incomplete
            progressPart2.setBackgroundColor(getResources().getColor(android.R.color.darker_gray));
        }
    }
}
