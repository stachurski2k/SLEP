document.addEventListener('DOMContentLoaded', () => {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const inputLabel = document.getElementById('input-label');
    const outputLabel = document.getElementById('output-label');
    const inputText = document.getElementById('input-text');
    const outputText = document.getElementById('output-text');
    const translateBtn = document.getElementById('translate-btn');
    const btnText = translateBtn.querySelector('.btn-text');
    const spinner = translateBtn.querySelector('.spinner');

    let currentMode = 'text2gloss';

    // Handle Tab Switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            currentMode = btn.dataset.mode;
            
            // Clear inputs
            inputText.value = '';
            outputText.value = '';

            // Update Labels
            if (currentMode === 'text2gloss') {
                inputLabel.textContent = 'English (Text)';
                outputLabel.textContent = 'American Sign Language (Glossy)';
                inputText.placeholder = 'Type your text here... e.g. I want to learn sign language.';
            } else {
                inputLabel.textContent = 'American Sign Language (Glossy)';
                outputLabel.textContent = 'English (Text)';
                inputText.placeholder = 'Type glosses here... e.g. ME WANT LEARN SIGN-LANGUAGE.';
            }
        });
    });

    // Handle Translation
    translateBtn.addEventListener('click', async () => {
        const text = inputText.value.trim();
        if (!text) {
            alert('Please enter text to translate!');
            return;
        }

        // UI Loading state
        translateBtn.disabled = true;
        btnText.textContent = 'Translating...';
        spinner.classList.remove('hidden');
        outputText.value = '';

        try {
            const endpoint = currentMode === 'text2gloss' ? '/api/text2gloss' : '/api/gloss2text';
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            const data = await response.json();
            
            if (response.ok) {
                // Typewriter effect
                typeWriter(data.result, outputText);
            } else {
                outputText.value = 'An error occurred during translation.';
            }
        } catch (error) {
            console.error('Error:', error);
            outputText.value = 'Connection error with the server.';
        } finally {
            // Restore UI
            translateBtn.disabled = false;
            btnText.textContent = 'Translate';
            spinner.classList.add('hidden');
        }
    });

    // Nice typewriter effect for output
    function typeWriter(text, element, speed = 20) {
        element.value = '';
        let i = 0;
        function type() {
            if (i < text.length) {
                element.value += text.charAt(i);
                i++;
                setTimeout(type, speed);
            }
        }
        type();
    }
});
