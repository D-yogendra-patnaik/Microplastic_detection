// Mobile menu functionality
const mobileMenuBtn = document.getElementById("mobileMenuBtn")
const mobileNav = document.getElementById("mobileNav")
const menuIcon = mobileMenuBtn.querySelector(".menu-icon")
const closeIcon = mobileMenuBtn.querySelector(".close-icon")

mobileMenuBtn.addEventListener("click", () => {
  const isOpen = !mobileNav.classList.contains("hidden")

  if (isOpen) {
    mobileNav.classList.add("hidden")
    menuIcon.classList.remove("hidden")
    closeIcon.classList.add("hidden")
  } else {
    mobileNav.classList.remove("hidden")
    menuIcon.classList.add("hidden")
    closeIcon.classList.remove("hidden")
  }
})

// Close mobile menu when clicking on a link
const mobileNavLinks = document.querySelectorAll(".mobile-nav-link")
mobileNavLinks.forEach((link) => {
  link.addEventListener("click", () => {
    mobileNav.classList.add("hidden")
    menuIcon.classList.remove("hidden")
    closeIcon.classList.add("hidden")
  })
})

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault()
    const target = document.querySelector(this.getAttribute("href"))
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      })
    }
  })
})

// Add some interactive hover effects for cards
const cards = document.querySelectorAll(".blog-card, .reference-card, .prototype-card")
cards.forEach((card) => {
  card.addEventListener("mouseenter", () => {
    card.style.transform = "translateY(-2px)"
    card.style.transition = "transform 0.2s ease"
  })

  card.addEventListener("mouseleave", () => {
    card.style.transform = "translateY(0)"
  })
})

// Add click handlers for blog titles and reference cards
document.querySelectorAll(".blog-title").forEach((title) => {
  title.addEventListener("click", () => {
    console.log("Navigate to blog post:", title.textContent)
  })
})

document.querySelectorAll(".reference-button").forEach((button) => {
  button.addEventListener("click", (e) => {
    const card = e.target.closest(".reference-card")
    const title = card.querySelector("h4").textContent
    console.log("Open reference:", title)
  })
})

// Add click handlers for CTA buttons
document.querySelectorAll(".primary-button, .secondary-button").forEach((button) => {
  button.addEventListener("click", () => {
    console.log("Button clicked:", button.textContent)
  })
})

// Chatbot functionality
document.addEventListener("DOMContentLoaded", () => {
  const chatInput = document.getElementById("chatInput")
  const sendButton = document.getElementById("sendButton")
  const chatMessages = document.getElementById("chatMessages")

  // Enable button only when input is not empty
  chatInput.addEventListener("input", () => {
    sendButton.disabled = chatInput.value.trim() === ""
  })

  // Handle Enter key press
  chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !sendButton.disabled) {
      sendMessage()
    }
  })

  sendButton.addEventListener("click", sendMessage)

  async function sendMessage() {
    const userMessage = chatInput.value.trim()
    if (!userMessage) return

    // Show user message
    addMessage(userMessage, "user")

    // Clear input
    chatInput.value = ""
    sendButton.disabled = true

    // Show typing indicator
    const typingDiv = addTypingIndicator()

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          message: userMessage,
          timestamp: new Date().toISOString(),
        }),
      })

      // Remove typing indicator
      typingDiv.remove()

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      const botReply = data.response || "⚠️ No response from server."

      // Show bot response
      addMessage(botReply, "bot")
    } catch (error) {
      console.error("Error:", error)
      // Remove typing indicator if still present
      if (typingDiv.parentNode) {
        typingDiv.remove()
      }
      addMessage("⚠️ Error connecting to server. Please check your backend configuration.", "bot")
    }
  }

  function addMessage(message, sender) {
    const messageDiv = document.createElement("div")
    messageDiv.className = `message ${sender}-message`

    if (sender === "user") {
      messageDiv.innerHTML = `
                <div class="message-avatar user-avatar">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                </div>
                <div class="message-content">
                    <div class="message-bubble user-bubble">${message}</div>
                </div>
            `
    } else {
      messageDiv.innerHTML = `
                <div class="message-avatar bot-avatar">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 8V4H8"></path>
                        <rect width="16" height="12" x="4" y="8" rx="2"></rect>
                        <path d="m9 16 0 0"></path>
                        <path d="m15 16 0 0"></path>
                    </svg>
                </div>
                <div class="message-content">
                    <div class="message-bubble bot-bubble">${message}</div>
                </div>
            `
    }

    chatMessages.appendChild(messageDiv)
    chatMessages.scrollTop = chatMessages.scrollHeight
    return messageDiv
  }

  function addTypingIndicator() {
    const typingDiv = document.createElement("div")
    typingDiv.className = "message bot-message"
    typingDiv.innerHTML = `
            <div class="message-avatar bot-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 8V4H8"></path>
                    <rect width="16" height="12" x="4" y="8" rx="2"></rect>
                    <path d="m9 16 0 0"></path>
                    <path d="m15 16 0 0"></path>
                </svg>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `
    chatMessages.appendChild(typingDiv)
    chatMessages.scrollTop = chatMessages.scrollHeight
    return typingDiv
  }

  // Initialize page
  mobileNav.classList.add("hidden")
  console.log("PRISM website initialized")
})
