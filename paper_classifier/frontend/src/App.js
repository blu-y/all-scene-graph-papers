import React, { useState, useEffect } from 'react';
import { Group, Panel, Separator } from 'react-resizable-panels';
import axios from 'axios';
import './App.css';
import PaperInfo from './components/PaperInfo';
import PDFViewer from './components/PDFViewer';
import CategoryTree from './components/CategoryTree';

const API_BASE = '';

function App() {
  const [currentPaper, setCurrentPaper] = useState(null);
  const [categories, setCategories] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedSubcategory, setSelectedSubcategory] = useState(null);
  const [currentClassification, setCurrentClassification] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [jumpNo, setJumpNo] = useState('');

  const showMessage = (text, type = 'info') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(''), 3000);
  };

  const loadPaper = async (no) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/api/papers/${no}`);
      setCurrentPaper(response.data);
      setJumpNo(response.data.no.toString());
      
      const classificationResponse = await axios.get(`${API_BASE}/api/papers/${no}/classification`);
      if (classificationResponse.data) {
        setCurrentClassification(classificationResponse.data);
        setSelectedCategory(classificationResponse.data.category);
        setSelectedSubcategory(classificationResponse.data.subcategory);
      } else {
        setCurrentClassification(null);
        setSelectedCategory(null);
        setSelectedSubcategory(null);
      }
    } catch (error) {
      showMessage(`Error loading paper: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/categories`);
      setCategories(response.data);
    } catch (error) {
      showMessage(`Error loading categories: ${error.message}`, 'error');
    }
  };

  const loadStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  // Load initial data
  useEffect(() => {
    const loadInitialPaper = async () => {
      try {
        // Use a very large number to start searching from the latest paper
        const response = await axios.get(`${API_BASE}/api/papers/9999/next`);
        const startPaper = response.data.next_no;
        if (startPaper) {
          loadPaper(startPaper);
        } else {
          // Fallback if none found
          const statsRes = await axios.get(`${API_BASE}/api/stats`);
          if (statsRes.data.total > 0) {
            loadPaper(statsRes.data.total); // Try loading the newest
          }
        }
      } catch (error) {
        console.error('Initial load failed:', error);
      }
    };

    loadCategories();
    loadStats();
    loadInitialPaper();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSaveAndNext = async () => {
    if (!currentPaper || !selectedCategory || !selectedSubcategory) {
      showMessage('Please select both category and subcategory', 'warning');
      return;
    }

    try {
      setLoading(true);
      
      // Save classification
      await axios.post(`${API_BASE}/api/classify`, {
        paper_no: currentPaper.no,
        category: selectedCategory,
        subcategory: selectedSubcategory
      });

      showMessage('Classification saved!', 'success');
      
      // Load next paper
      const nextResponse = await axios.get(`${API_BASE}/api/papers/${currentPaper.no}/next`);
      
      if (nextResponse.data.next_no) {
        await loadPaper(nextResponse.data.next_no);
      } else {
        const statsRes = await axios.get(`${API_BASE}/api/stats`);
        showMessage('All papers classified!', 'success');
        if (statsRes.data.total > 0) {
           loadPaper(statsRes.data.total);
        }
      }
      
      await loadStats();
    } catch (error) {
      showMessage(`Error saving classification: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = async () => {
    if (!currentPaper) return;

    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/api/papers/${currentPaper.no}/next`);
      
      if (response.data.next_no) {
        await loadPaper(response.data.next_no);
      } else {
        showMessage('No more papers to classify', 'info');
      }
    } catch (error) {
      showMessage(`Error loading next paper: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleFinish = async () => {
    if (!window.confirm('Are you sure you want to complete the classification? \nThis will save the current paper, generate markdown files and shut down the server.')) {
      return;
    }

    try {
      setLoading(true);

      // Save current paper first if categories are selected
      if (currentPaper && selectedCategory && selectedSubcategory) {
        showMessage('Saving current paper...', 'info');
        await axios.post(`${API_BASE}/api/classify`, {
          paper_no: currentPaper.no,
          category: selectedCategory,
          subcategory: selectedSubcategory
        });
      }

      showMessage('Generating markdown files and shutting down...', 'info');
      await axios.post(`${API_BASE}/api/finish`);
      
      // Wait a bit and show a final message
      setTimeout(() => {
        alert('Classification process completed. The browser window can now be closed.');
      }, 1000);
    } catch (error) {
      showMessage(`Error finishing classification: ${error.message}`, 'error');
      setLoading(false);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        handleSaveAndNext();
      } else if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        handleSkip();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPaper, selectedCategory, selectedSubcategory]);

  const handlePrevious = async () => {
    if (!currentPaper || !stats) return;

    try {
      setLoading(true);
      const currentNo = currentPaper.no;
      // Go to next paper number (older)
      const nextNo = currentNo < stats.total ? currentNo + 1 : stats.total;
      await loadPaper(nextNo);
    } catch (error) {
      showMessage(`Error loading previous paper: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleNext = async () => {
    if (!currentPaper) return;

    try {
      setLoading(true);
      const currentNo = currentPaper.no;
      // Go to previous paper number (newer)
      const nextNo = currentNo > 1 ? currentNo - 1 : 1;
      await loadPaper(nextNo);
    } catch (error) {
      showMessage(`Error loading next paper: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleJump = async (e) => {
    e.preventDefault();
    const no = parseInt(jumpNo);
    if (isNaN(no) || no < 1 || (stats && no > stats.total)) {
      showMessage(`Invalid paper number. Please enter a number between 1 and ${stats?.total || '?'}`, 'warning');
      return;
    }
    await loadPaper(no);
  };

  const handleAddCategory = async (categoryData) => {
    try {
      await axios.post(`${API_BASE}/api/categories`, categoryData);
      await loadCategories();
      showMessage('Category added successfully', 'success');
    } catch (error) {
      showMessage(`Error adding category: ${error.message}`, 'error');
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>📄 Paper Classifier</h1>
        {stats && (
          <div className="stats">
            Classified: {stats.classified} / {stats.total} ({stats.percentage}%)
          </div>
        )}
      </header>

      {message && (
        <div className={`message message-${message.type}`}>
          {message.text}
        </div>
      )}

    <div className="main-content">
        <Group direction="horizontal">
          <Panel defaultSize={30} minSize={20}>
            <div className="panel left-panel">
              {currentPaper && <PaperInfo paper={currentPaper} />}
            </div>
          </Panel>
          <Separator className="resize-handle" />
          <Panel defaultSize={50} minSize={30}>
            <div className="panel center-panel">
              {currentPaper && (
                <PDFViewer paperNo={currentPaper.no} apiBase={API_BASE} />
              )}
            </div>
          </Panel>
          <Separator className="resize-handle" />
          <Panel defaultSize={20} minSize={15}>
            <div className="panel right-panel">
              {categories && (
                <CategoryTree
                  categories={categories}
                  selectedCategory={selectedCategory}
                  selectedSubcategory={selectedSubcategory}
                  currentClassification={currentClassification}
                  onSelectCategory={setSelectedCategory}
                  onSelectSubcategory={setSelectedSubcategory}
                  onAddCategory={handleAddCategory}
                />
              )}
            </div>
          </Panel>
        </Group>
      </div>

      <footer className="app-footer">
        <div className="footer-left">
          <button
            type="button"
            onClick={handlePrevious}
            disabled={loading || !currentPaper || !stats || currentPaper.no >= stats.total}
            className="btn btn-secondary"
          >
            ← Previous
          </button>
          <button
            type="button"
            onClick={handleNext}
            disabled={loading || !currentPaper || currentPaper.no <= 1}
            className="btn btn-secondary"
          >
            Next →
          </button>
          <form className="jump-form" onSubmit={handleJump}>
            <input
              type="number"
              placeholder="No."
              value={jumpNo}
              onChange={(e) => setJumpNo(e.target.value)}
              className="jump-input"
            />
            <button type="submit" className="btn btn-secondary btn-small">Go</button>
          </form>
        </div>
        <div className="footer-right">
          <button
            type="button"
            onClick={handleSkip}
            disabled={loading || !currentPaper}
            className="btn btn-secondary"
          >
            Skip (Ctrl+N)
          </button>
          <button
            type="button"
            onClick={handleSaveAndNext}
            disabled={loading || !currentPaper || !selectedCategory || !selectedSubcategory}
            className="btn btn-primary"
          >
            {loading ? 'Saving...' : 'Save & Next (Ctrl+S)'}
          </button>
          <button
            type="button"
            onClick={handleFinish}
            disabled={loading}
            className="btn btn-success"
            style={{ marginLeft: '10px' }}
          >
            Classified Complete
          </button>
        </div>
      </footer>
    </div>
  );
}

export default App;
