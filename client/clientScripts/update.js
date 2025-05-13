const BASE_API = "https://l4wefjcn1i.execute-api.us-east-1.amazonaws.com/dev";
const UPDATE_API_URL = `${BASE_API}/update`;

// ✅ Add this email validation function
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email.toLowerCase());
}

document.getElementById("update-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const oldEmail = document.getElementById("old-email").value.trim();
  const newEmail = document.getElementById("new-email").value.trim();
  const messageEl = document.getElementById("update-message");

  messageEl.textContent = "";
  messageEl.className = "message";

  if (!validateEmail(oldEmail) || !validateEmail(newEmail)) {
    messageEl.textContent = "Please enter valid email addresses.";
    messageEl.classList.add("error");
    return;
  }

  try {
    const response = await fetch(UPDATE_API_URL, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ old_email: oldEmail, new_email: newEmail })
    });

    const result = await response.json();

    if (!response.ok) {
      messageEl.textContent = result.error || "Failed to update email.";
      messageEl.classList.add("error");
    } else {
      messageEl.textContent = result.message || "Email updated successfully.";
      messageEl.classList.add("success");
    }
  } catch (err) {
    messageEl.textContent = "Network error. Please try again.";
    messageEl.classList.add("error");
  }
});
