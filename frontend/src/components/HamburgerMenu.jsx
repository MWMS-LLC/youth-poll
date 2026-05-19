import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAudio } from '../contexts/AudioContext.jsx'

const HamburgerMenu = () => {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  
  // Use global audio context for theme song state
  const { isThemeSongOn, toggleThemeSong } = useAudio()

  const handleNavigate = (path) => {
    setOpen(false)
    if (location.pathname !== path) {
      navigate(path)
    }
  }

  // Utility function to clear localStorage and start fresh
  const _clearLocalStorageAndRefresh = () => {
    try {
      // Clear all localStorage data
      localStorage.clear()
      
      // Show a brief message
      alert('Data cleared! The page will refresh to start fresh.')
      
      // Refresh the page
      window.location.reload()
    } catch (error) {
      console.error('Error clearing localStorage:', error)
      alert('Error clearing data. Please try refreshing the page manually.')
    }
  }

  const handleSoundtrackNavigate = () => {
    setOpen(false)
    navigate('/soundtrack')
  }

  return (
    <div style={styles.container}>
      <button
        style={styles.hamburgerButton}
        onClick={() => { window.location.href = 'https://myworldmysay.com' }}
        aria-label="Go to home"
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={styles.hamburgerIcon}>
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
      </button>

      {/* Hamburger Icon */}
      <button
        style={styles.hamburgerButton}
        onClick={() => setOpen((prev) => !prev)}
        aria-label="Open menu"
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={styles.hamburgerIcon}>
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
      
      {/* Dropdown Menu */}
      {open && (
        <div style={styles.dropdownMenu}>
          <button 
            style={styles.beforeYouBeginItem} 
            onClick={() => handleNavigate('/before-you-begin')}
          >
            Before You Begin
          </button>
          <button 
            style={styles.menuItem} 
            onClick={() => handleNavigate('/')}
          >
            Pick a Topic
          </button>
          <button 
            style={styles.menuItem} 
            onClick={handleSoundtrackNavigate}
          >
            MyWorld Soundtrack 🎧
          </button>
          <button 
            style={styles.menuItem} 
            onClick={() => handleNavigate('/faq')}
          >
            About/FAQ
          </button>
          <button 
            style={styles.menuItem} 
            onClick={() => handleNavigate('/help')}
          >
            Help/Resources
          </button>
          
          {/* Theme Song Toggle */}
          <div style={styles.toggleContainer}>
            <span style={styles.toggleLabel}>Theme Song 🎧</span>
            <label style={styles.toggleSwitch}>
              <input 
                type="checkbox" 
                checked={isThemeSongOn} 
                onChange={toggleThemeSong} 
                style={styles.toggleInput} 
              />
              <div style={{
                ...styles.toggleSlider,
                backgroundColor: isThemeSongOn ? '#4ECDC4' : '#95A5A6'
              }}></div>
            </label>
          </div>


        </div>
      )}
    </div>
  )
}

const styles = {
  container: {
    position: 'fixed',
    top: '16px',
    right: '16px',
    zIndex: 50,
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  
  hamburgerButton: {
    width: '48px',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '50%',
    background: 'rgba(255, 255, 255, 0.2)',
    border: 'none',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
  },
  
  hamburgerIcon: {
    color: 'white'
  },
  
  dropdownMenu: {
    position: 'absolute',
    right: 0,
    top: '100%',
    marginTop: '8px',
    width: '240px',
    background: 'rgba(20, 20, 20, 0.95)',
    backdropFilter: 'blur(15px)',
    color: 'white',
    borderRadius: '20px',
    boxShadow: '0 25px 50px rgba(0, 0, 0, 0.5)',
    padding: '20px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    zIndex: 50
  },
  
  menuItem: {
    textAlign: 'left',
    padding: '12px 16px',
    borderRadius: '12px',
    background: 'transparent',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: '500',
    transition: 'all 0.2s ease',
    fontFamily: 'inherit',
    ':hover': {
      background: 'rgba(255, 255, 255, 0.1)',
      color: 'white'
    }
  },

  beforeYouBeginItem: {
    textAlign: 'left',
    padding: '12px 16px',
    borderRadius: '12px',
    background: '#FF8C00',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: '600',
    transition: 'all 0.2s ease',
    fontFamily: 'inherit',
    boxShadow: '0 2px 8px rgba(255, 140, 0, 0.3)',
    ':hover': {
      background: '#FF7F00',
      color: 'white',
      boxShadow: '0 4px 12px rgba(255, 140, 0, 0.4)'
    }
  },

  toggleContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 16px',
    marginTop: '10px',
    borderTop: '1px solid rgba(255, 255, 255, 0.1)'
  },

  toggleLabel: {
    color: 'white',
    fontSize: '16px',
    fontWeight: '500'
  },

  toggleSwitch: {
    position: 'relative',
    display: 'inline-block',
    width: '50px',
    height: '24px'
  },

  toggleInput: {
    opacity: 0,
    width: 0,
    height: 0
  },

  toggleSlider: {
    position: 'absolute',
    cursor: 'pointer',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderRadius: '24px',
    transition: '0.3s',
    '&:before': {
      position: 'absolute',
      content: '""',
      height: '18px',
      width: '18px',
      left: '3px',
      bottom: '3px',
      backgroundColor: 'white',
      borderRadius: '50%',
      transition: '0.3s'
    }
  },

  debugContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    padding: '12px 16px',
    marginTop: '10px',
    borderTop: '1px solid rgba(255, 255, 255, 0.1)'
  },

  debugButton: {
    padding: '8px 12px',
    backgroundColor: 'rgba(78, 205, 196, 0.2)',
    color: 'rgba(255, 255, 255, 0.9)',
    border: '1px solid rgba(78, 205, 196, 0.3)',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'all 0.2s ease',
    fontFamily: 'inherit'
  }
}

export default HamburgerMenu
