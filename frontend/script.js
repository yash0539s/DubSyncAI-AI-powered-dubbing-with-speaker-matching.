
  document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("uploadForm").addEventListener("submit", async function(e) {
      e.preventDefault();

      const fileInput = document.getElementById("file");
      const lang = document.getElementById("language").value;

      if (!fileInput.files[0]) {
        alert("Please select a file.");
        return;
      }

      const formData = new FormData();
      formData.append("file", fileInput.files[0]);

      // ✅ Set backend URL explicitly
      const backendUrl = "http://127.0.0.1:8000/dub/?target_lang=" + encodeURIComponent(lang);

      try {
        const res = await fetch(backendUrl, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const errorText = await res.text();
          alert("Error generating dub: " + errorText);
          return;
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);

        const video = document.getElementById("dubbedVideo");
        video.src = url;
        video.classList.remove("hidden");

        document.getElementById("output").classList.remove("hidden");
      } catch (err) {
        alert("❌ Error sending request: " + err.message);
        console.error(err);
      }
    });
  });
