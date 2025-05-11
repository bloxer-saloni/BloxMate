import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom"; // Import useNavigate
import {
  Box,
  Grid,
  Typography,
  Paper,
  Button,
  IconButton,
  TextField,
  InputAdornment,
  Divider,
  AppBar,
  Toolbar,
  createTheme,
  ThemeProvider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Link
} from "@mui/material";
import SendIcon from '@mui/icons-material/Send';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import WorkIcon from '@mui/icons-material/Work';
import PolicyIcon from '@mui/icons-material/Policy';
import FolderSharedIcon from '@mui/icons-material/FolderShared';
import SchoolIcon from '@mui/icons-material/School';
import DnsIcon from '@mui/icons-material/Dns';
import PeopleIcon from '@mui/icons-material/People';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import MessageIcon from '@mui/icons-material/Message';

// Infoblox colors theme
const infobloxTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00FF85', // Bright green
      light: '#5aff9f',
      dark: '#00cc6a',
      contrastText: '#121921',
    },
    secondary: {
      main: '#cccc00', // Darker yellow
      light: '#e0e000',
      dark: '#999900',
      contrastText: '#121921',
    },
    background: {
      default: '#121921', // Dark blue/black
      paper: '#1e2732',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b3b3b3',
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e2732',
        },
      },
    },
  },
});

// Updated list of chatbot capabilities with your requested topics
const chatbotCapabilities = [
  { 
    id: 'products_resources', 
    title: 'Products & Resources', 
    description: 'Information from Infoblox documentation archives', 
    icon: <DnsIcon sx={{ color: '#00FF85' }} />
  },
  { 
    id: 'organization', 
    title: 'Organization Chart', 
    description: 'Find people and their roles to reach out for specific needs', 
    icon: <PeopleIcon sx={{ color: '#cccc00' }} />
  },
  { 
    id: 'onboarding', 
    title: 'Onboarding Material', 
    description: 'Resources and information for new team members', 
    icon: <MenuBookIcon sx={{ color: '#00FF85' }} />
  },
  { 
    id: 'communication', 
    title: 'Workplace Communication', 
    description: 'Guidance for difficult conversations with managers and colleagues', 
    icon: <MessageIcon sx={{ color: '#cccc00' }} />
  },
  { 
    id: 'access', 
    title: 'Access & Setup', 
    description: 'Help with system access, permissions, and technical setup', 
    icon: <AccountCircleIcon sx={{ color: '#00FF85' }} />
  },
];

export default function ChatBot() {
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate(); // Hook for navigation

  // Initialize with welcome message
  useEffect(() => {
    setChatMessages([{ 
      sender: 'bot', 
      text: 'Hello! I\'m the BloxMate Assistant. How can I help you today? You can ask me about Infoblox products, learning resources, company policies, and more.' 
    }]);
  }, []);

  // Handle back button click
  const handleBackClick = () => {
    navigate("/home"); // Navigate to the home page
  };

  // Handle LinkedIn Learning button click
  const handleLinkedInClick = () => {
    navigate("/learnings-dashboard"); // Navigate to LearningsDashboard.js
  };

  // Handle logout button click
  const handleLogout = () => {
    navigate("/home"); // Redirect to HomePage
  };

  // Updated handleChatSubmit function to call the backend API
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    // Add user message to chat
    const newUserMessage = { sender: 'user', text: chatInput };
    setChatMessages([...chatMessages, newUserMessage]);
    
    // Show typing indicator
    setIsLoading(true);
    
    try {
      console.log("Attempting to connect to backend API at http://localhost:5000/api/chat");
      
      // Call the backend API
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: chatInput }),
      });
      
      console.log("Backend response status:", response.status);
      
      const data = await response.json();
      console.log("Backend response data:", data);
      
      if (data.success) {
        // Process the response message to handle formatting
        const processedMessage = processAgentResponse(data.message);
        setChatMessages(prev => [...prev, { sender: 'bot', text: processedMessage }]);
      } else {
        setChatMessages(prev => [...prev, { 
          sender: 'bot', 
          text: `Error from backend: ${data.error || "Unknown error occurred"}`
        }]);
      }
    } catch (error) {
      console.error('Error communicating with the agent:', error);
      setChatMessages(prev => [...prev, { 
        sender: 'bot', 
        text: `I'm having trouble connecting to my backend services (${error.message}). Please make sure the Flask server is running at http://localhost:5000.`
      }]);
    } finally {
      setIsLoading(false);
      setChatInput("");
    }
  };
  
  // Function to process the agent response and format it for display
  const processAgentResponse = (response) => {
    // Remove routing headers that might be confusing in the UI
    let processedResponse = response
      .replace(/🤔 Analyzing your question\.\.\./, '')
      .replace(/📚 Routing to Knowledge Base Agent\.\.\./, '')
      .replace(/🎓 Routing to Learning Assistant\.\.\./, '')
      .replace(/👥 Routing to Org Chart Assistant\.\.\./, '')
      .replace(/🤝 Routing to Workplace Communication Assistant\.\.\./, '')
      .replace(/🚀 Routing to Onboarding Assistant\.\.\./, '')
      .trim();
    
    // Add formatting for headers
    processedResponse = processedResponse
      // Format section headers (lines followed by ':' or ending with ':')
      .replace(/^([A-Z][^:]+):$/gm, '<strong style="color: #00FF85">$1:</strong>')
      .replace(/^([A-Z][^:]+:\s)/gm, '<strong style="color: #00FF85">$1</strong>')
      
      // Highlight person names and titles
      .replace(/\b([A-Z][a-z]+ [A-Z][a-z]+)( - )([^,]+)/g, '<strong>$1</strong>$2<em>$3</em>')
      
      // Format any bullet points with better spacing
      .replace(/\n[\s]*[-•*][\s]+([^\n]+)/g, '<br/>• $1')
      
      // Format numbered lists
      .replace(/\n[\s]*(\d+)\.[\s]+([^\n]+)/g, '<br/>$1. $2')
      
      // Add proper paragraph spacing
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>')
      
      // Highlight important words
      .replace(/\*\*([^*]+)\*\*/g, '<strong style="color: #cccc00">$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      
      // Highlight key terms, dates, and URLs
      .replace(/\b(https?:\/\/[^\s]+)\b/g, '<a href="$1" target="_blank" style="color: #00FF85">$1</a>')
      .replace(/\b(\d{1,2}\/\d{1,2}\/\d{2,4})\b/g, '<span style="color: #cccc00">$1</span>')
      .replace(/\b(FY\d{2})\b/g, '<span style="color: #cccc00">$1</span>');
    
    return processedResponse;
  };

  // Updated box style for capability rectangles with reduced height
  const capabilityBoxStyle = {
    p: 1.5, // Reduced padding
    borderRadius: 1,
    border: '1px solid',
    borderColor: 'rgba(255, 255, 255, 0.1)', // Lighter border to appear less interactive
    mb: 1.5, // Reduced margin between boxes
    cursor: 'default', // Default cursor instead of pointer
    backgroundColor: 'rgba(30, 39, 50, 0.6)', // Slightly different background
    position: 'relative',
    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      pointerEvents: 'none', // Make sure it doesn't interfere with text selection
    }
  };

  return (
    <ThemeProvider theme={infobloxTheme}>
      <Box sx={{ bgcolor: 'background.default', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* Header with enhanced BloxMate title */}
        <AppBar position="static" sx={{ bgcolor: '#121921', borderBottom: '1px solid #00FF85' }}>
          <Toolbar>
            <IconButton
              edge="start"
              color="primary"
              onClick={handleBackClick} // Updated to use handleBackClick
              sx={{ mr: 2 }}
            >
              <ArrowBackIcon />
            </IconButton>
            <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center' }}>
              <Typography 
                variant="h4" 
                component="div" 
                sx={{ 
                  fontWeight: "bold", 
                  textAlign: "center",
                  color: "#ffffff",
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
            </Box>
            <Button 
              variant="outlined" 
              onClick={handleLogout} 
              sx={{ 
                borderColor: '#ffffff', 
                color: '#ffffff', 
                ml: 2, 
                '&:hover': { 
                  bgcolor: 'rgba(255, 255, 255, 0.1)' 
                } 
              }}
            >
              Logout
            </Button>
          </Toolbar>
        </AppBar>

        {/* Main Content */}
        <Box sx={{ p: 4, flex: 1 }}>
          <Grid container spacing={4} sx={{ flexWrap: 'nowrap' }}>
            {/* Left Column - Button and Info Boxes */}
            <Grid md={4} sx={{ flexShrink: 0 }}>
              {/* LinkedIn Learning Button */}
              <Button
                variant="contained"
                startIcon={<LinkedInIcon />}
                onClick={handleLinkedInClick} // Navigate to LearningsDashboard.js
                fullWidth
                sx={{
                  mb: 4,
                  mt: -2,
                  py: 1.5,
                  bgcolor: '#0077B5', // LinkedIn blue
                  '&:hover': {
                    bgcolor: '#006097', // Darker LinkedIn blue
                  },
                  fontSize: '1rem',
                  fontWeight: 'bold',
                }}
              >
                Access LinkedIn Learning
              </Button>

              {/* What can this chatbot answer section */}
              <Paper elevation={3} sx={{ p: 2, mb: 1, borderTop: '2px solid #cccc00', mt:-2 }}>
                <Typography 
                  variant="h5" 
                  gutterBottom 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    color: '#cccc00',
                    mb: 3
                  }}
                >
                  <QuestionAnswerIcon sx={{ mr: 1 }} />
                  Topics BloxMate Can Help With
                </Typography>

                {/* Non-clickable capability info boxes */}
                {chatbotCapabilities.map((capability) => (
                  <Box 
                    key={capability.id} 
                    sx={{ 
                      ...capabilityBoxStyle,
                      borderLeft: capability.id % 2 === 0 ? 
                        '3px solid rgba(0, 255, 133, 0.7)' : 
                        '3px solid rgba(204, 204, 0, 0.7)', // Updated yellow shade
                    }}
                    role="region" // ARIA role for accessibility
                    aria-label={`Information about ${capability.title}`}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {capability.icon}
                      <Typography variant="h6" sx={{ ml: 1, color: 'text.primary' }}>
                        {capability.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      {capability.description}
                    </Typography>
                  </Box>
                ))}
                
                {/* Add a helper text to clarify these are just informational */}
                {/* <Typography 
                  variant="caption" 
                  sx={{ 
                    display: 'block', 
                    textAlign: 'center', 
                    mt: 1, 
                    color: 'text.secondary',
                    fontStyle: 'italic'
                  }}
                >
                  These are examples of topics I can assist with. Ask me in the chat!
                </Typography> */}
              </Paper>
            </Grid>

            {/* Right Column - Chatbot Interface */}
            <Grid md={8} sx={{ flexGrow: 1 }}>
              <Paper 
                elevation={3} 
                sx={{ 
                  height: 'calc(100vh - 120px)', // Increased height
                  display: 'flex', 
                  flexDirection: 'column',
                  borderTop: '2px solid #00FF85',
                  p: 0,
                  overflow: 'hidden',
                  mt: -1.5,
                }}
              >
                {/* Chat Header */}
                <Box sx={{ p: 2, borderBottom: '1px solid rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center'}}>
                  <HelpOutlineIcon sx={{ mr: 1, color: '#00FF85' }} />
                  <Typography variant="h6" sx={{ color: 'text.primary' }}>
                    Chat with BloxMate Assistant
                  </Typography>
                </Box>

                {/* Chat Messages Area */}
                <Box 
                  sx={{ 
                    p: 3,
                    flex: 1, 
                    overflowY: 'auto',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2,
                  }}
                >
                  {chatMessages.map((message, index) => (
                    <Box 
                      key={index} 
                      sx={{ 
                        alignSelf: message.sender === 'user' ? 'flex-end' : 'flex-start',
                        maxWidth: '70%',
                        p: 2,
                        borderRadius: 2,
                        height: 'auto',
                        bgcolor: message.sender === 'user' ? 'rgba(0, 255, 133, 0.2)' : 'rgba(204, 204, 0, 0.1)',
                        border: message.sender === 'user' ? 
                          '1px solid rgba(0, 255, 133, 0.5)' : 
                          '1px solid rgba(204, 204, 0, 0.3)'
                      }}
                    >
                      <Typography variant="body1" color="text.primary">
                        {message.sender === 'bot' ? (
                          <div dangerouslySetInnerHTML={{ __html: message.text }} />
                        ) : (
                          message.text
                        )}
                      </Typography>
                    </Box>
                  ))}
                  
                  {/* Loading indicator */}
                  {isLoading && (
                    <Box 
                      sx={{ 
                        alignSelf: 'flex-start',
                        p: 2,
                        borderRadius: 2,
                        bgcolor: 'rgba(204, 204, 0, 0.1)',
                        border: '1px solid rgba(204, 204, 0, 0.3)',
                        display: 'flex',
                        alignItems: 'center'
                      }}
                    >
                      <Typography variant="body1" color="text.primary" sx={{ mr: 1 }}>
                        BloxMate is thinking
                      </Typography>
                      <Box sx={{ display: 'flex' }}>
                        <Box 
                          sx={{ 
                            width: '8px', 
                            height: '8px', 
                            borderRadius: '50%', 
                            bgcolor: '#00FF85',
                            animation: 'pulse 1s infinite',
                            animationDelay: '0s',
                            mx: 0.5,
                            '@keyframes pulse': {
                              '0%': { opacity: 0.3 },
                              '50%': { opacity: 1 },
                              '100%': { opacity: 0.3 },
                            }
                          }} 
                        />
                        <Box 
                          sx={{ 
                            width: '8px', 
                            height: '8px', 
                            borderRadius: '50%', 
                            bgcolor: '#00FF85',
                            animation: 'pulse 1s infinite',
                            animationDelay: '0.2s',
                            mx: 0.5
                          }} 
                        />
                        <Box 
                          sx={{ 
                            width: '8px', 
                            height: '8px', 
                            borderRadius: '50%', 
                            bgcolor: '#00FF85',
                            animation: 'pulse 1s infinite',
                            animationDelay: '0.4s',
                            mx: 0.5
                          }} 
                        />
                      </Box>
                    </Box>
                  )}
                </Box>

                {/* Chat Input */}
                <Box sx={{ p: 2, borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <form onSubmit={handleChatSubmit}>
                    <TextField
                      fullWidth
                      placeholder="Ask me anything about company resources, products, or learning..."
                      variant="outlined"
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      disabled={isLoading}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && isLoading) {
                          e.preventDefault();
                        }
                      }}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          '& fieldset': { borderColor: 'rgba(0, 255, 133, 0.5)' },
                          '&:hover fieldset': { borderColor: '#00FF85' },
                          '&.Mui-focused fieldset': { borderColor: '#00FF85' },
                          '&.Mui-disabled': { 
                            opacity: 0.7,
                            '& fieldset': { borderColor: 'rgba(204, 204, 0, 0.3)' }
                          }
                        },
                      }}
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton type="submit" color="primary" disabled={isLoading}>
                              <SendIcon />
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                  </form>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </Box>

        {/* Footer */}
        <Box sx={{ bgcolor: '#1e2732', py: 2, textAlign: 'center', borderTop: '1px solid #00FF85' }}>
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            © {new Date().getFullYear()} <span style={{ fontWeight: "bold", color: "#ffffff" }}>BloxMate</span>. All rights reserved. |{" "}
            <Link href="https://www.infoblox.com" target="_blank" rel="noopener" sx={{ color: '#00FF85', ml: 1 }}>
              Visit Infoblox
            </Link>
          </Typography>
        </Box>
      </Box>
    </ThemeProvider>
  );
}
