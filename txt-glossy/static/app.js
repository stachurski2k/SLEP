document.addEventListener('DOMContentLoaded', () => {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const inputLabel = document.getElementById('input-label');
    const outputLabel = document.getElementById('output-label');
    const inputText = document.getElementById('input-text');
    const outputText = document.getElementById('output-text');
    const translateBtn = document.getElementById('translate-btn');
    const btnText = translateBtn.querySelector('.btn-text');
    const spinner = translateBtn.querySelector('.spinner');

    const modelIndicator = document.getElementById('model-indicator');
    const runBenchmarkBtn = document.getElementById('run-benchmark-btn');
    const benchmarkResults = document.getElementById('benchmark-results');
    const benchmarkContent = document.getElementById('benchmark-content');

    let currentMode = 'text2gloss';

    // Fetch model info
    fetch('/api/model_info')
        .then(res => res.json())
        .then(data => {
            modelIndicator.textContent = 'Model: ' + (data.model || 'Unknown');
        })
        .catch(err => console.error('Error fetching model info:', err));

    // Handle benchmark
    runBenchmarkBtn.addEventListener('click', async () => {
        if (benchmarkResults.classList.contains('hidden')) {
            benchmarkResults.classList.remove('hidden');
        }
        benchmarkContent.innerHTML = 'Running benchmark... Please wait (this may take a minute).';
        runBenchmarkBtn.disabled = true;

        try {
            const response = await fetch('/api/benchmark');
            const data = await response.json();
            
            if (data.error) {
                benchmarkContent.innerHTML = `<span style="color: #ff6b6b;">Error: ${data.error}</span>`;
            } else {
                benchmarkContent.innerHTML = `
                    <p style="margin:0 0 0.5rem 0;"><strong>Text ➔ Gloss:</strong> BLEU: ${data.text_to_gloss.bleu} | ROUGE-1: ${data.text_to_gloss.rouge1}</p>
                    <p style="margin:0 0 0.5rem 0;"><strong>Gloss ➔ Text:</strong> BLEU: ${data.gloss_to_text.bleu} | ROUGE-1: ${data.gloss_to_text.rouge1}</p>
                    <p style="margin:0; font-size: 0.8rem; color: #aaa;">Tested on ${data.sample_count} sample pairs.</p>
                `;
            }
        } catch (error) {
            console.error('Benchmark error:', error);
            benchmarkContent.innerHTML = `<span style="color: #ff6b6b;">Failed to fetch benchmark results.</span>`;
        } finally {
            runBenchmarkBtn.disabled = false;
            runBenchmarkBtn.textContent = 'Run Benchmark Again';
        }
    });

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
