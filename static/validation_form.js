document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form");
  if (!form) return;

  const fields = ["sugar", "fat", "energy", "carbs", "protein"];

  form.addEventListener("submit", function (e) {
    let formValid = true;

    fields.forEach(fieldName => {
      const field = document.querySelector(`input[name="${fieldName}"]`);
      if (!field) return;

      const value = field.value.trim();
      field.style.border = "1px solid #42A475"; // Reset to default

      // Skip empty fields (they are optional)
      if (!value) return;

      const number = parseFloat(value);
      const isValidNumber = !isNaN(number) && number >= 0;

      if (!isValidNumber) {
        field.style.border = "2px solid red";
        formValid = false;
      }
    });

    if (!formValid) {
      e.preventDefault();
      alert("Please correct the highlighted fields. Only positive numbers are allowed.");
    }
  });
});
