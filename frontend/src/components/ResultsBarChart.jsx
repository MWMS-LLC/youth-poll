import React from 'react'

const ResultsBarChart = ({ results, _questionText, options = [] }) => {
  // Helper function to get option text from options data
  const getOptionText = (option) => {
    if (options && options.length > 0) {
      const foundOption = options.find(opt => opt.option_select === option)
      if (foundOption) {
        return foundOption.option_text
      }
    }
    // Fallback to generic option text if no options data available
    const genericTexts = {
      'A': 'Unpaired. Unbothered. Still in orbit.',
      'B': 'Pairing mode on. Still blinking ...',
      'C': 'Connected. Kinda laggy. But we\'re updating.',
      'D': 'Patch notes dropping soon. Heart.exe rebooting.',
      'OTHER': 'Write your own'
    }
    return genericTexts[option] || `Option ${option}`
  }

  // Safety check - if no results, show empty state
  if (!results || !results.results || results.results.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyState}>
          No votes yet. Be the first to vote! 🎉
        </div>
        
        <div style={styles.totalResponses}>
          Total votes: 0
        </div>
      </div>
    )
  }

  // Always calculate total votes so multi-select questions sum to 100%
  const totalVotes = results.results.reduce((sum, item) => {
    const count = parseFloat(item.votes) || 0
    if (isNaN(count) || count < 0) {
      console.warn('Invalid votes value:', item.votes, 'for option:', item.option_select)
      return sum
    }
    return sum + count
  }, 0)
  
  // Keep track of backend total responses (fallback when no votes yet)
  const totalResponses = results.total_responses || 0
  
  // Denominator for percentages (use total votes, fallback to total responses)
  const percentageBase = totalVotes > 0 ? totalVotes : totalResponses
  
  // Transform data for progress bars with safety checks
  const chartData = results.results.map(item => {
    const count = parseFloat(item.votes) || 0
    
    if (isNaN(count) || count < 0) {
      console.warn('Skipping invalid votes:', item.votes, 'for option:', item.option_select)
      return null
    }
    
    const percentage = percentageBase > 0 ? Math.round((count / percentageBase) * 100) : 0
    
    if (isNaN(percentage) || percentage < 0) {
      console.warn('Invalid percentage calculated:', percentage, 'for option:', item.option_select)
      return null
    }
    
    return {
      option: item.option_select || 'Unknown',
      count: count,
      percentage: percentage
    }
  }).filter(item => item !== null && item.option !== 'Unknown')

  // Ensure we have valid data
  if (chartData.length === 0 || percentageBase === 0 || isNaN(percentageBase)) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyState}>
          No valid data available
        </div>
        
        <div style={styles.totalResponses}>
          Total votes: 0
        </div>
      </div>
    )
  }

  const totalLabelValue = Math.round(totalVotes > 0 ? totalVotes : totalResponses)
  const totalLabelPrefix = 'Total votes'

  return (
    <div style={styles.container}>

      {/* Results with Horizontal Progress Bars */}
      <div style={styles.resultsContainer}>
        {chartData.map((item, index) => (
          <div key={index} style={styles.resultItem}>
            <div style={styles.optionHeader}>
              <span style={styles.optionLabel}>
                {getOptionText(item.option)}
              </span>
              <span style={styles.percentage}>
                {item.percentage}%
              </span>
            </div>
            
            {/* Progress Bar */}
            <div style={styles.progressBarContainer}>
              <div 
                style={{
                  ...styles.progressBar,
                  width: `${item.percentage}%`
                }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Total Responses */}
      <div style={styles.totalResponses}>
        {totalLabelPrefix}: {totalLabelValue}
      </div>
    </div>
  )
}

// Professional dark theme styling that matches your app
const styles = {
  container: {
    backgroundColor: 'transparent',
    padding: '30px',
    borderRadius: '0',
    border: 'none',
    boxShadow: 'none',
    backdropFilter: 'none',
    marginBottom: '20px'
  },
  
  questionBox: {
    backgroundColor: '#FFD93D',
    padding: '20px',
    borderRadius: '16px',
    marginBottom: '25px',
    color: '#333',
    fontSize: '18px',
    lineHeight: '1.6',
    fontWeight: '500',
    boxShadow: '0 4px 15px rgba(255, 217, 61, 0.3)'
  },
  
  emptyState: {
    padding: '40px 20px',
    color: 'rgba(0, 0, 0, 0.6)',
    fontSize: '16px',
    textAlign: 'center',
    fontStyle: 'italic'
  },
  
  resultsContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    marginBottom: '25px'
  },
  
  resultItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px'
  },
  
  optionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px'
  },
  
  optionLabel: {
    fontWeight: '600',
    color: 'white',
    fontSize: '16px',
    flex: 1,
    marginRight: '15px'
  },
  
  percentage: {
    backgroundColor: '#2D7D7A',
    color: 'white',
    padding: '6px 12px',
    borderRadius: '20px',
    fontWeight: 'bold',
    fontSize: '14px',
    minWidth: '50px',
    textAlign: 'center',
    boxShadow: '0 2px 8px rgba(45, 125, 122, 0.3)'
  },
  
  progressBarContainer: {
    width: '100%',
    height: '12px',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: '6px',
    overflow: 'hidden',
    boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.2)'
  },
  
  progressBar: {
    height: '100%',
    background: 'linear-gradient(90deg, #2D7D7A 0%, #4ECDC4 100%)',
    borderRadius: '6px',
    transition: 'width 0.8s ease-out',
    boxShadow: '0 2px 8px rgba(45, 125, 122, 0.4)',
    minWidth: '4px'
  },
  
  totalResponses: {
    textAlign: 'center',
    padding: '18px',
    backgroundColor: 'rgba(45, 125, 122, 0.1)',
    borderRadius: '16px',
    fontWeight: 'bold',
    color: '#2D7D7A',
    fontSize: '16px',
    border: '1px solid rgba(45, 125, 122, 0.2)'
  }
}

export default ResultsBarChart
