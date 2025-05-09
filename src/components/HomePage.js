import React from "react";
import { Box, Typography, Button, AppBar, Toolbar, Link, createTheme, ThemeProvider } from "@mui/material";
import { useNavigate } from "react-router-dom";

// BloxMate theme
const bloxMateTheme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#00FF85", // Bright green
    },
    secondary: {
      main: "#cccc00", // Yellow
    },
    background: {
      default: "#121921", // Dark background
      paper: "#1e2732",
    },
    text: {
      primary: "#ffffff",
      secondary: "#b3b3b3",
    },
  },
});

export default function HomePage() {
  const navigate = useNavigate();

  // Handle "Get Started" button click
  const handleGetStarted = () => {
    navigate("/"); // Redirect to ChatBot
  };

  return (
    <ThemeProvider theme={bloxMateTheme}>
      <Box sx={{ bgcolor: "background.default", minHeight: "100vh", display: "flex", flexDirection: "column", position: "relative" }}>
        {/* Header with enhanced BloxMate title */}
        <AppBar position="static" sx={{ bgcolor: "#121921", borderBottom: "1px solid #00FF85" }}>
          <Toolbar>
            <Typography 
              variant="h4" 
              sx={{ 
                flexGrow: 1, 
                marginLeft: "100px",
                fontWeight: "bold", 
                color: "#ffffff",
                textAlign: "center",
                fontSize: "2.5rem", // Larger text
                letterSpacing: "1px", // Add letter spacing
                textShadow: "0 0 10px rgba(0, 255, 133, 0.5)", // Add glow effect
                "& span": {
                  background: "linear-gradient(90deg, #00FF85 30%, #cccc00 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  fontSize: "2.7rem", // Even larger for "Mate"
                  fontWeight: 900, // Bolder
                }
              }}
            >
              Blox<span>Mate</span>
            </Typography>
            <Button
              variant="outlined"
              onClick={handleGetStarted}
              sx={{
                borderColor: "#ffffff",
                color: "#ffffff",
                "&:hover": { bgcolor: "rgba(255, 255, 255, 0.1)" },
              }}
            >
              Get Started
            </Button>
          </Toolbar>
        </AppBar>

        {/* <Box
        sx={{
            position: "absolute",
            top: "50%",
            left: "90%",
            transform: "translate(-50%, -50%)",
            width: 600,
            height: 600,
            clipPath: "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)",
            zIndex: 0,
            background: "linear-gradient(45deg, #00FF85, #FFFF00)",
            boxShadow: `
            0 0 15px #00FF85,
            0 0 30px #FFFF00,
            0 0 45px #00FF85,
            0 0 60px #FFFF00
            `,
            border: "none",
            opacity: 0.3
        }}
        /> */}


        {/* Main Content */}
        <Box
          sx={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            position: "absolute",
            top: "20%",
            left: "30%",
            width: "150px",
            opacity: 0.8,
            zIndex: 1,
          }}
        />
        

        {/* Main Content */}
        <Box
          sx={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            p: 4,
            textAlign: "center",
            zIndex: 2, // Ensure content is above the background
          }}
        >
          <Typography variant="h2" sx={{ fontWeight: "bold", color: "#ffffff", mb: 2 }}>
            Welcome to BloxMate
          </Typography>
          <Typography variant="h5" sx={{ color: "#00FF85", mb: 4 }}>
            Your Corporate Journey Assistant
          </Typography>
          <Typography variant="body1" sx={{ color: "text.secondary", maxWidth: "600px", mb: 4 }}>
            BloxMate is here to answer all your questions, assist with onboarding, and guide you throughout your corporate journey. Simplify your work life with BloxMate.
          </Typography>
          <Button
            variant="contained"
            onClick={handleGetStarted}
            sx={{
              bgcolor: "#00FF85",
              color: "#121921",
              fontWeight: "bold",
              px: 4,
              py: 1.5,
              "&:hover": { bgcolor: "#00cc6a" },
            }}
          >
            Get Started
          </Button>
        </Box>

        {/* Footer */}
        <Box sx={{ bgcolor: "#1e2732", py: 2, textAlign: "center", borderTop: "1px solid #00FF85", zIndex: 2 }}>
          <Typography variant="body2" sx={{ color: "text.secondary" }}>
            © {new Date().getFullYear()} <span style={{ fontWeight: "bold", color: "#ffffff" }}>BloxMate</span>. All rights reserved. |{" "}
            <Link href="https://www.infoblox.com" target="_blank" rel="noopener" sx={{ color: "#00FF85" }}>
              Visit Infoblox
            </Link>
          </Typography>
        </Box>
      </Box>
    </ThemeProvider>
  );
}
