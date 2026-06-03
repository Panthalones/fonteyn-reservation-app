const API_URL = "https://fonteyn-backend.graymushroom-75e4e72a.swedencentral.azurecontainerapps.io";

const msalConfig = {
  auth: {
    clientId: "d44500dc-fe0b-4fe1-9769-72796d5bfec2",
    authority: "https://login.microsoftonline.com/b4d2af65-2275-461f-8eff-82709d98fb52",
    redirectUri: window.location.origin + "/admin.html"
  }
};

const loginSection = document.querySelector("#loginSection");
const adminSection = document.querySelector("#adminSection");
const loginBtn = document.querySelector("#loginBtn");
const logoutBtn = document.querySelector("#logoutBtn");
const refreshBtn = document.querySelector("#refreshBtn");
const reservationsTable = document.querySelector("#reservationsTable");
const adminMessage = document.querySelector("#adminMessage");
const loginMessage = document.querySelector("#loginMessage");

let msalInstance;

document.addEventListener("DOMContentLoaded", async () => {
  try {
    if (typeof msal === "undefined") {
      loginMessage.textContent =
        "MSAL library is niet geladen. Controleer je internetverbinding of script-link.";
      loginMessage.style.color = "red";
      return;
    }

    msalInstance = new msal.PublicClientApplication(msalConfig);

    const response = await msalInstance.handleRedirectPromise();

    if (response && response.account) {
      msalInstance.setActiveAccount(response.account);
    }

    const accounts = msalInstance.getAllAccounts();

    if (accounts.length > 0) {
      msalInstance.setActiveAccount(accounts[0]);
      showAdminPage();
      loadReservations();
    } else {
      showLoginPage();
    }
  } catch (error) {
    console.error("MSAL startup error:", error);
    loginMessage.textContent = "Fout bij starten van Entra ID login. Check F12 Console.";
    loginMessage.style.color = "red";
    showLoginPage();
  }
});

if (loginBtn) {
  loginBtn.addEventListener("click", async () => {
    try {
      loginMessage.textContent = "Je wordt doorgestuurd naar Microsoft...";
      loginMessage.style.color = "#1f4d3a";

      await msalInstance.loginRedirect({
        scopes: ["User.Read"],
        prompt: "select_account"
      });
    } catch (error) {
      console.error("Login error:", error);
      loginMessage.textContent = "Login starten is mislukt. Check F12 Console.";
      loginMessage.style.color = "red";
    }
  });
}

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    msalInstance.logoutRedirect({
      postLogoutRedirectUri: window.location.origin + "/admin.html"
    });
  });
}

if (refreshBtn) {
  refreshBtn.addEventListener("click", loadReservations);
}

function showLoginPage() {
  loginSection.style.display = "block";
  adminSection.style.display = "none";
}

function showAdminPage() {
  loginSection.style.display = "none";
  adminSection.style.display = "block";
}

async function loadReservations() {
  try {
    adminMessage.textContent = "Reservaties worden geladen...";
    adminMessage.style.color = "#1f4d3a";

    const response = await fetch(`${API_URL}/api/reservations`);
    const reservations = await response.json();

    if (!response.ok) {
      adminMessage.textContent = "Fout bij ophalen: " + reservations.error;
      adminMessage.style.color = "red";
      return;
    }

    renderReservations(reservations);

    adminMessage.textContent = "Reservaties succesvol geladen.";
    adminMessage.style.color = "green";
  } catch (error) {
    console.error(error);
    adminMessage.textContent = "Kan geen verbinding maken met de backend.";
    adminMessage.style.color = "red";
  }
}

function renderReservations(reservations) {
  reservationsTable.innerHTML = "";

  if (!reservations || reservations.length === 0) {
    reservationsTable.innerHTML = `
      <tr>
        <td colspan="11">Geen reservaties gevonden.</td>
      </tr>
    `;
    return;
  }

  reservations.forEach((reservation) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${reservation.id}</td>
      <td>${reservation.full_name}</td>
      <td>${reservation.email}</td>
      <td>${reservation.park}</td>
      <td>${reservation.accommodation}</td>
      <td>${formatDate(reservation.arrival_date)}</td>
      <td>${formatDate(reservation.departure_date)}</td>
      <td>${reservation.guests}</td>
      <td>€${Number(reservation.total_price || 0).toFixed(2)}</td>
      <td>${reservation.status}</td>
      <td>
        <button class="delete-btn" onclick="deleteReservation(${reservation.id})">
          Verwijderen
        </button>
      </td>
    `;

    reservationsTable.appendChild(row);
  });
}

async function deleteReservation(id) {
  const confirmDelete = confirm(
    "Weet je zeker dat je reservatie " + id + " wilt verwijderen?"
  );

  if (!confirmDelete) {
    return;
  }

  try {
    const response = await fetch(`${API_URL}/api/reservations/${id}`, {
      method: "DELETE"
    });

    const result = await response.json();

    if (response.ok) {
      adminMessage.textContent = "Reservatie succesvol verwijderd.";
      adminMessage.style.color = "green";
      loadReservations();
    } else {
      adminMessage.textContent = "Fout bij verwijderen: " + result.error;
      adminMessage.style.color = "red";
    }
  } catch (error) {
    console.error(error);
    adminMessage.textContent = "Kan geen verbinding maken met de backend.";
    adminMessage.style.color = "red";
  }
}

function formatDate(dateValue) {
  if (!dateValue) {
    return "-";
  }

  return String(dateValue).split("T")[0];
}