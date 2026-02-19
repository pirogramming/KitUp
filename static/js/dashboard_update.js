document.getElementById("project_image").addEventListener("change", function () {
    const file = this.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById("preview_image").src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
});