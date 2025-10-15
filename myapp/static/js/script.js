    const bookBtn = document.getElementById('bookBtn');
    const appointmentBox = document.getElementById('appointmentBox');
    const confirmBtn = document.getElementById('confirmBtn');
    const otpBox = document.getElementById('otpBox');
    const slots = document.querySelectorAll('.slot-btn');
    const inputs = document.querySelectorAll('.otp-input');

    // Step 1: Show appointment form
    bookBtn.addEventListener('click', () => {
        appointmentBox.classList.remove('d-none');
        bookBtn.classList.add('d-none');
    });

    // Step 2: Slot selection
    slots.forEach(slot => {
        slot.addEventListener('click', () => {
            slots.forEach(s => s.classList.remove('selected'));
            slot.classList.add('selected');
        });
    });

    // Step 3: Confirm & show OTP
    confirmBtn.addEventListener('click', () => {
        const date = document.getElementById('appointmentDate').value;
        const selectedSlot = document.querySelector('.slot-btn.selected');

        if (!date || !selectedSlot) {
            alert("Please select a date and a slot first.");
            return;
        }

        appointmentBox.classList.add('d-none');
        otpBox.classList.remove('d-none');
        inputs[0].focus();
    });

    // Step 4: OTP auto-focus
    inputs.forEach((input, index) => {
        input.addEventListener('input', () => {
            if (input.value && index < inputs.length - 1) {
                inputs[index + 1].focus();
            }
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === "Backspace" && index > 0 && !input.value) {
                inputs[index - 1].focus();
            }
        });
    });