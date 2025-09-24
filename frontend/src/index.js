import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { MantineProvider, createTheme } from '@mantine/core';
import App from './App';
import './index.css';
import '@mantine/core/styles.css';

// Create a custom theme
const theme = createTheme({
  colors: {
    primary: ['#E7F5FF', '#D0EBFF', '#A5D8FF', '#74C0FC', '#4DABF7', '#339AF0', '#228BE6', '#1C7ED6', '#1971C2', '#1864AB'],
  },
  primaryColor: 'primary',
  fontFamily: 'Roboto, sans-serif',
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <MantineProvider theme={theme}>
        <App />
      </MantineProvider>
    </BrowserRouter>
  </React.StrictMode>
);