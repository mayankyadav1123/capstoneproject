/*
 * SaafGaadi — Frontend Script (script.js)
 * ========================================
 * Uses fetch() API with async/await to communicate
 * with the Flask backend at http://127.0.0.1:5000.
 *
 * NO Supabase SDK used on the frontend.
 * All database operations go through the Flask API.
 */

// ── Flask Backend Base URL ──
var API_BASE = "";


// ─────────────────────────────────────
// 1.  BOOK A SERVICE  (POST /api/book)
// ─────────────────────────────────────

/**
 * Sends booking data to the Flask backend.
 * Called when the user clicks "Book Now" on a service card.
 *
 * @param {string} userName     - Customer's full name
 * @param {string} phoneNumber  - Phone with country code e.g. "+919876543210"
 * @param {string} serviceType  - One of: "daily_plan", "quick_wash", "nearby_center"
 */
async function createBooking(userName, phoneNumber, serviceType) {
  try {
    var response = await fetch(API_BASE + "/api/book", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        user_name: userName,
        phone_number: phoneNumber,
        service_type: serviceType
      })
    });

    var result = await response.json();

    if (!response.ok) {
      console.error("Booking API error:", result.error);
      alert("Booking failed — " + result.error);
      return null;
    }

    console.log("Booking success:", result);
    return result;
  } catch (err) {
    console.error("Network error:", err);
    alert("Could not connect to the server. Make sure Flask is running.");
    return null;
  }
}


// ──────────────────────────────────────────
// 2.  FETCH ALL BOOKINGS  (GET /api/bookings)
// ──────────────────────────────────────────

/**
 * Fetches bookings from the Flask backend.
 * Optionally filters by phone number.
 *
 * @param  {string} [phone] - Optional phone to filter
 * @return {Array}           - Array of booking objects
 */
async function fetchBookings(phone) {
  try {
    var url = API_BASE + "/api/bookings";
    if (phone) {
      url += "?phone=" + encodeURIComponent(phone);
    }

    var response = await fetch(url);
    var result = await response.json();

    if (!response.ok) {
      console.error("Fetch bookings error:", result.error);
      return [];
    }

    console.log("Fetched bookings:", result.data);
    return result.data;
  } catch (err) {
    console.error("Network error:", err);
    return [];
  }
}


// ─────────────────────────────────────────────
// 3.  DASHBOARD — Wire up service card buttons
// ─────────────────────────────────────────────

/*
 * We listen for clicks on the "View →" buttons inside the
 * Services tab.  Each button opens a small booking prompt
 * and sends data to the Flask API via createBooking().
 */

document.addEventListener("DOMContentLoaded", function () {

  // ── Load saved user info from localStorage ──
  var userName = localStorage.getItem("sg_user_name") || "User";
  var userPhone = localStorage.getItem("sg_user_phone") || "";

  // Personalize the dashboard
  var greeting = document.querySelector(".navbar-greeting");
  if (greeting) greeting.textContent = "Welcome, " + userName.split(" ")[0] + "!";

  var avatar = document.getElementById("user-avatar");
  if (avatar) avatar.textContent = userName.charAt(0).toUpperCase();

  // Service card mapping  (button id → service_type key)
  var serviceButtons = {
    "btn-view-daily":  "daily_plan",
    "btn-view-quick":  "quick_wash",
    "btn-view-nearby": "nearby_center"
  };

  // Attach click handlers — uses stored user info, no prompts
  Object.keys(serviceButtons).forEach(function (btnId) {
    var btn = document.getElementById(btnId);
    if (!btn) return;

    btn.addEventListener("click", function (e) {
      e.preventDefault();

      var serviceType = serviceButtons[btnId];

      if (!userName || !userPhone) {
        alert("Please register first!");
        window.location.href = "/";
        return;
      }

      // Call the Flask API with stored user info
      handleBooking(userName, userPhone, serviceType, btn);
    });
  });


  // ── Handle the async booking call ──
  async function handleBooking(name, phone, serviceType, btn) {
    var originalText = btn.textContent;
    btn.textContent = "Booking…";
    btn.style.pointerEvents = "none";

    var result = await createBooking(name, phone, serviceType);

    if (result) {
      btn.textContent = "Booked ✓";
      setTimeout(function () {
        btn.textContent = originalText;
        btn.style.pointerEvents = "auto";
      }, 2000);
    } else {
      btn.textContent = originalText;
      btn.style.pointerEvents = "auto";
    }
  }


  // ─────────────────────────────────────────────────
  // 4.  "YOUR SERVICES" TAB — Load bookings on click
  // ─────────────────────────────────────────────────

  var yourServicesTab = document.getElementById("tab-your-services");
  if (yourServicesTab) {
    yourServicesTab.addEventListener("click", function () {
      renderBookings();
    });
  }

  /**
   * Fetches bookings from the backend and renders them
   * as cards inside the #panel-your-services section.
   */
  async function renderBookings() {
    var panel = document.getElementById("panel-your-services");
    if (!panel) return;

    // Show a loading state
    var grid = panel.querySelector(".card-grid");
    if (!grid) return;

    grid.innerHTML = '<p style="color:#999;text-align:center;padding:24px;">Loading bookings…</p>';

    var bookings = await fetchBookings();

    if (bookings.length === 0) {
      grid.innerHTML = '<p style="color:#999;text-align:center;padding:24px;">No bookings found. Book a service first! 🚗</p>';
      return;
    }

    // Status icons and service labels
    var statusIcons = { pending: "⏳", confirmed: "✅", completed: "⭐", cancelled: "❌" };
    var svcLabels   = {
      daily_plan:     "Daily Car Wash Plan",
      quick_wash:     "Quick Car Wash",
      nearby_center:  "Nearby Service Center"
    };

    // Build cards
    var html = "";
    for (var i = 0; i < bookings.length; i++) {
      var b     = bookings[i];
      var icon  = statusIcons[b.status] || "📋";
      var label = svcLabels[b.service_type] || b.service_type;
      var date  = new Date(b.created_at).toLocaleString("en-IN", {
        day: "numeric", month: "short", year: "numeric",
        hour: "2-digit", minute: "2-digit"
      });

      html +=
        '<div class="card">' +
          '<div class="card-icon">' + icon + '</div>' +
          '<h2 class="card-title">' + label + '</h2>' +
          '<p class="card-desc">' +
            '<strong>Name:</strong> '   + b.user_name + '<br>' +
            '<strong>Phone:</strong> '  + b.phone_number + '<br>' +
            '<strong>Status:</strong> ' + b.status.charAt(0).toUpperCase() + b.status.slice(1) + '<br>' +
            '<strong>Booked:</strong> ' + date +
          '</p>' +
          '<span class="card-btn" style="cursor:default;">' + icon + ' ' + b.status.charAt(0).toUpperCase() + b.status.slice(1) + '</span>' +
        '</div>';
    }

    grid.innerHTML = html;
  }
});
