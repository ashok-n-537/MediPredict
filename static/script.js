
document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("symptomForm");
    const searchBox = document.getElementById("symptomSearch");
    const count = document.getElementById("count");
    const result = document.getElementById("result");
    const noSymptoms = document.getElementById("noSymptoms");
    const predictButton = document.getElementById("predictButton");

    // Check that the required HTML elements exist
    if (!form || !result || !predictButton) {
        console.error("MediPredict: Required HTML elements not found.");
        return;
    }

    // Get selected symptoms
    function getSelectedSymptoms() {
        return Array.from(
            document.querySelectorAll('input[name="symptoms"]:checked')
        ).map(item => item.value);
    }

    // Update selected symptom count
    function updateCount() {
        if (count) {
            count.textContent =
                getSelectedSymptoms().length + " symptoms selected";
        }
    }

    document.querySelectorAll('input[name="symptoms"]').forEach(box => {
        box.addEventListener("change", updateCount);
    });

    // Search symptoms
    if (searchBox) {
        searchBox.addEventListener("input", function () {
            const value = searchBox.value.toLowerCase().trim();
            const cards = document.querySelectorAll(".symptom-card");
            let visible = 0;

            cards.forEach(card => {
                const match = card.textContent.toLowerCase().includes(value);
                card.style.display = match ? "" : "none";
                if (match) visible++;
            });

            if (noSymptoms) {
                noSymptoms.style.display = visible === 0 ? "block" : "none";
            }
        });
    }

    // Display messages
    function showMessage(message, type) {
        result.innerHTML = "";
        result.style.display = "block";
        result.className = "mp-result mp-result-" + type;

        const paragraph = document.createElement("p");
        paragraph.textContent = message;
        result.appendChild(paragraph);
    }

    // Display successful prediction
    function showPrediction(data, symptoms) {
        result.innerHTML = "";
        result.style.display = "block";
        result.className = "mp-result mp-result-success";

        const label = document.createElement("p");
        label.className = "mp-result-label";
        label.textContent = "✓ AI ANALYSIS COMPLETE";

        const heading = document.createElement("h3");
        heading.textContent = "Your Prediction Result";

        const caption = document.createElement("p");
        caption.textContent = "Possible condition identified:";

        const prediction = document.createElement("div");
        prediction.className = "mp-predicted-condition";
        prediction.textContent = data.prediction;

        const message = document.createElement("p");
        message.textContent = data.message || "Prediction saved successfully.";

        const symptomHeading = document.createElement("h4");
        symptomHeading.textContent = "Symptoms you selected";

        const symptomList = document.createElement("div");
        symptomList.className = "mp-result-symptoms";

        symptoms.forEach(symptom => {
            const chip = document.createElement("span");
            chip.className = "mp-result-chip";
            chip.textContent = symptom.replace(/_/g, " ");
            symptomList.appendChild(chip);
        });

        const disclaimer = document.createElement("p");
        disclaimer.className = "mp-result-disclaimer";
        disclaimer.textContent =
            "Important: This is an educational machine-learning prediction, not a medical diagnosis. Please consult a qualified healthcare professional for medical advice.";

        result.append(
            label,
            heading,
            caption,
            prediction,
            message,
            symptomHeading,
            symptomList,
            disclaimer
        );

        result.scrollIntoView({
            behavior: "smooth",
            block: "nearest"
        });
    }

    // Submit symptoms to Flask
    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const symptoms = getSelectedSymptoms();

        if (symptoms.length === 0) {
            showMessage("Please select at least one symptom.", "error");
            return;
        }

        predictButton.disabled = true;
        predictButton.textContent = "Analyzing...";

        showMessage("Analyzing your symptoms. Please wait...", "loading");

        try {
            const response = await fetch("/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    symptoms: symptoms
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Prediction failed.");
            }

            if (!data.prediction) {
                throw new Error("No prediction was returned by the server.");
            }

            showPrediction(data, symptoms);

        } catch (error) {
            showMessage("Error: " + error.message, "error");

        } finally {
            predictButton.disabled = false;
            predictButton.textContent = "Analyze Symptoms";
        }
    });

    updateCount();
});
