import React, { useState, useEffect } from "react";
import { 
  Box, 
  Grid, 
  Typography, 
  Paper, 
  List, 
  ListItem, 
  ListItemText, 
  Avatar, 
  Checkbox,
  TextField,
  Button,
  IconButton,
  InputAdornment,
  AppBar,
  Toolbar,
  createTheme,
  ThemeProvider,
  Link,
  CircularProgress
} from "@mui/material";
import { useNavigate } from "react-router-dom"; // Import useNavigate
import SendIcon from '@mui/icons-material/Send';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
// import LearningImage from '../images/image.png';

// Updated Infoblox colors theme with darker yellow
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

// Mock function to simulate the LinkedIn API call
// In a real app, you would make an API call to a backend that uses the Python code
const mockFetchLinkedInCourses = async (query) => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Generate mock course data based on the query
  return [
    { 
      title: `${query} Essential Training`, 
      link: `https://www.linkedin.com/learning/courses/${query.toLowerCase().replace(/\s+/g, '-')}-essential-training` 
    },
    { 
      title: `Advanced ${query} Techniques`, 
      link: `https://www.linkedin.com/learning/courses/advanced-${query.toLowerCase().replace(/\s+/g, '-')}` 
    },
    { 
      title: `${query} for Beginners`, 
      link: `https://www.linkedin.com/learning/courses/${query.toLowerCase().replace(/\s+/g, '-')}-beginners` 
    }
  ];
};

export default function LearningsDashboard() {
  // State for learning items (checklist)
  const [learningItems, setLearningItems] = useState([
    { id: 1, text: "AI Fundamentals (Suggested by Manager)", completed: false },
  ]);
  
  // State for chatbot
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  
  // Automatically display bot's welcome message on load
  useEffect(() => {
    setChatMessages([{ sender: 'bot', text: 'What would you like to learn today?' }]);
  }, []);
  
  // State for LinkedIn course suggestions
  const [suggestedCourses, setSuggestedCourses] = useState([]);
  const [isLoadingCourses, setIsLoadingCourses] = useState(false);

  const navigate = useNavigate(); // Hook for navigation
  
  // Handle back button click
  const handleBackClick = () => {
    navigate("/"); // Navigate back to ChatBot.js
  };

  // Handle logout button click
  const handleLogout = () => {
    navigate("/home"); // Redirect to HomePage
  };
  
  // Handle checkbox toggle
  const handleToggleItem = (id) => {
    setLearningItems(
      learningItems.map(item => 
        item.id === id ? { ...item, completed: !item.completed } : item
      )
    );
  };

  
  // Fetch LinkedIn courses based on user input
  const fetchCourses = async (query) => {
    setIsLoadingCourses(true);
    try {
      const courses = await mockFetchLinkedInCourses(query);
      setSuggestedCourses(courses);
    } catch (error) {
      console.error("Error fetching courses:", error);
    } finally {
      setIsLoadingCourses(false);
    }
  };
  
  // Handle chat submission
  const handleChatSubmit = (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    // Add user message to chat
    const newUserMessage = { sender: 'user', text: chatInput };
    setChatMessages([...chatMessages, newUserMessage]);
    
    // Store the query for course fetching
    const query = chatInput;
    
    // Simulate bot response and add course suggestion
    setTimeout(() => {
      // Bot response
      const botMessage = { 
        sender: 'bot', 
        text: `I suggest learning about "${query}". I've added it to your list and found some LinkedIn courses for you.` 
      };
      setChatMessages(messages => [...messages, botMessage]);
      
      // Add to learning items
      const newId = learningItems.length > 0 ? Math.max(...learningItems.map(item => item.id)) + 1 : 1;
      setLearningItems(items => [...items, { id: newId, text: query, completed: false }]);
      
      // Fetch LinkedIn courses for this topic
      fetchCourses(query);
    }, 500);
    
    setChatInput("");
  };

  return (
    <ThemeProvider theme={infobloxTheme}>
      <Box sx={{ bgcolor: "background.default", minHeight: "100vh", display: 'flex', flexDirection: 'column' }}>
        {/* Header with enhanced BloxMate title */}
        <AppBar position="static" sx={{ bgcolor: '#121921', borderBottom: '1px solid #00FF85' }}>
          <Toolbar>
            <IconButton
              edge="start"
              color="primary"
              onClick={handleBackClick} // Navigate back to ChatBot.js
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

        <Box sx={{ p: 4, flex: 1 }}>
          <Grid container spacing={4} sx={{ flexWrap: 'nowrap' }}>
            {/* Sidebar */}
            <Grid item xs={4} sx={{ flexShrink: 0, width: '30%' }}>
              <Paper sx={{ p: 2, mb: 2, borderTop: '2px solid #00FF85' }} elevation={3}>
                <Typography variant="h6" gutterBottom sx={{ color: '#ffffff' }}>Things to Learn</Typography>
                <List dense>
                  {learningItems.map((item) => (
                    <ListItem key={item.id} disablePadding>
                      <Checkbox 
                        checked={item.completed} 
                        onChange={() => handleToggleItem(item.id)}
                        sx={{ 
                          '& .MuiSvgIcon-root': { fontSize: 20 },
                          color: '#00FF85',
                          '&.Mui-checked': {
                            color: '#00FF85',
                          }
                        }}
                      />
                      <ListItemText 
                        primary={item.text} 
                        sx={{ 
                          textDecoration: item.completed ? 'line-through' : 'none',
                          color: item.completed ? 'text.secondary' : 'text.primary'
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Paper>

              {/* <Paper sx={{ p: 2, mb: 2, borderTop: '2px solid #FFFF00' }} elevation={3}>
                <Typography variant="h6" gutterBottom sx={{ color: '#ffffff' }}>Ongoing Courses</Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Avatar variant="square" sx={{ bgcolor: '#00FF85', width: 40, height: 40 }} />
                  <Avatar variant="square" sx={{ bgcolor: '#FFFF00', width: 40, height: 40, color: '#121921' }} />
                </Box>
              </Paper> */}

              <Paper sx={{ p: 2, mb: 2, borderTop: '2px solid #cccc00' }} elevation={3}>
                <Typography variant="h6" sx={{ color: '#cccc00' }}>Suggested Courses</Typography>
                {isLoadingCourses ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                    <CircularProgress size={24} color="primary" />
                  </Box>
                ) : suggestedCourses.length > 0 ? (
                  <List dense>
                    {suggestedCourses.map((course, index) => (
                      <ListItem key={index} disablePadding sx={{ mb: 1 }}>
                        <ListItemText 
                          primary={
                            <Link 
                              href={course.link} 
                              target="_blank" 
                              rel="noopener"
                              sx={{ 
                                color: '#00FF85',
                                textDecoration: 'none',
                                '&:hover': {
                                  textDecoration: 'underline'
                                }
                              }}
                            >
                              {course.title}
                            </Link>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Ask the Course Assistant to get LinkedIn course suggestions
                  </Typography>
                )}
              </Paper>
              {/* Chatbot at the end of courses section */}
              <Paper sx={{ p: 2, mt: 2, borderTop: '2px solid #FFFF00', height: 300, display: 'flex', flexDirection: 'column' }} elevation={3}>
              <Typography variant="h6" gutterBottom sx={{ color: '#ffffff' }}>Course Assistant</Typography>
              <Box sx={{ flex: 1, overflowY: 'auto', mb: 2 }}>
                {chatMessages.map((message, index) => (
                  <Box 
                    key={index} 
                    sx={{ 
                      textAlign: message.sender === 'user' ? 'right' : 'left',
                      mb: 1,
                      p: 1,
                      bgcolor: message.sender === 'user' ? 'rgba(0, 255, 133, 0.2)' : 'rgba(255, 255, 0, 0.1)',
                      borderRadius: 1,
                      display: 'inline-block',
                      maxWidth: '80%',
                      float: message.sender === 'user' ? 'right' : 'left',
                      clear: 'both',
                      border: message.sender === 'user' 
                        ? '1px solid rgba(0, 255, 133, 0.5)' 
                        : '1px solid rgba(255, 255, 0, 0.3)'
                    }}
                  >
                    <Typography variant="body2" color="text.primary">{message.text}</Typography>
                  </Box>
                ))}
              </Box>
              <form onSubmit={handleChatSubmit}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Enter a topic to learn"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton type="submit" edge="end" sx={{ color: '#00FF85' }}>
                          <SendIcon />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </form>
            </Paper>
            </Grid>

            {/* Main content - image */}
            <Grid item xs={8} sx={{ flexGrow: 1 }}>
  <Paper elevation={3} sx={{ 
    height: '100%', 
    width: '100%', 
    background: '#121921',
    p: 0, // No padding
    m: 0, // No margin
    borderRadius: 0,
    overflow: 'hidden',
  }}>
    <Box sx={{ height: '100%', width: '100%' }}>
      <Box
        component="img"
        src={require('../images/image.png')}
        alt="Top Half"
        sx={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          display: 'block',
        }}
      />
      
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
