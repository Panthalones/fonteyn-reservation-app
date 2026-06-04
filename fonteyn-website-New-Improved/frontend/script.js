const API_URL = "https://fonteyn-backend.graymushroom-75e4e72a.swedencentral.azurecontainerapps.io";

const menuBtn = document.querySelector("#menuBtn");
const navMenu = document.querySelector("#navMenu");
const bookingForm = document.querySelector("#bookingForm");
const formMessage = document.querySelector("#formMessage");

if (menuBtn && navMenu) {
  menuBtn.addEventListener("click", () => {
    navMenu.classList.toggle("open");
  });
}

if (bookingForm) {
  bookingForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const reservationData = {
      full_name: document.querySelector("#fullName").value.trim(),
      email: document.querySelector("#email").value.trim(),
      phone: document.querySelector("#phone").value.trim(),
      park: document.querySelector("#park").value,
      accommodation: document.querySelector("#accommodation").value,
      arrival_date: document.querySelector("#arrivalDate").value,
      departure_date: document.querySelector("#departureDate").value,
      guests: Number(document.querySelector("#guests").value),
      extras: document.querySelector("#extras").value.trim(),
      total_price: calculatePrice()
    };

    try {
      formMessage.textContent = "Reservatie wordt opgeslagen...";
      formMessage.style.color = "#1f4d3a";

      const response = await fetch(`${API_URL}/api/reservations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(reservationData)
      });

      const result = await response.json();

      if (response.ok) {
        formMessage.textContent =
          "Reservatie succesvol opgeslagen! Reservatie ID: " +
          result.reservation_id;

        formMessage.style.color = "green";
        bookingForm.reset();
      } else {
        formMessage.textContent =
          "Fout bij opslaan: " + result.error;

        formMessage.style.color = "red";
      }
    } catch (error) {
      console.error(error);

      formMessage.textContent =
        "Kan geen verbinding maken met de backend.";

      formMessage.style.color = "red";
    }
  });
}

function calculatePrice() {
  const accommodation = document.querySelector("#accommodation").value;
  const guests = Number(document.querySelector("#guests").value);

  let basePrice = 0;

  if (accommodation === "Luxe Cottage") {
    basePrice = 189;
  } else if (accommodation === "Familiehuis") {
    basePrice = 149;
  } else if (accommodation === "Kampeerplaats") {
    basePrice = 49;
  }

  return basePrice * guests;
}