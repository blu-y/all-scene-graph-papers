import React, { useState } from 'react';

function CategoryTree({
  categories,
  selectedCategory,
  selectedSubcategory,
  currentClassification,
  onSelectCategory,
  onSelectSubcategory,
  onAddCategory
}) {
  // Initialize with all categories expanded
  const [expandedCategories, setExpandedCategories] = useState(() => {
    if (!categories || !categories.categories) return {};
    const expanded = {};
    Object.keys(categories.categories).forEach(catName => {
      expanded[catName] = true;
    });
    return expanded;
  });
  const [showAddCategory, setShowAddCategory] = useState(false);
  const [showAddSubcategory, setShowAddSubcategory] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryDesc, setNewCategoryDesc] = useState('');
  const [newSubcategoryName, setNewSubcategoryName] = useState('');
  const [newSubcategoryDesc, setNewSubcategoryDesc] = useState('');

  const toggleCategory = (catName) => {
    setExpandedCategories(prev => ({
      ...prev,
      [catName]: !prev[catName]
    }));
  };

  const handleSelectSubcategory = (catName, subName) => {
    onSelectCategory(catName);
    onSelectSubcategory(subName);
  };

  const handleAddCategory = () => {
    if (newCategoryName && newCategoryDesc) {
      onAddCategory({
        category: newCategoryName,
        description: newCategoryDesc
      });
      setNewCategoryName('');
      setNewCategoryDesc('');
      setShowAddCategory(false);
    }
  };

  const handleAddSubcategory = () => {
    if (selectedCategory && newSubcategoryName && newSubcategoryDesc) {
      onAddCategory({
        parent_category: selectedCategory,
        subcategory: newSubcategoryName,
        description: newSubcategoryDesc
      });
      setNewSubcategoryName('');
      setNewSubcategoryDesc('');
      setShowAddSubcategory(false);
    }
  };

  if (!categories || !categories.categories) {
    return <div>Loading categories...</div>;
  }

  return (
    <div className="category-tree">
      <h3>Categories</h3>
      
      {selectedCategory && selectedSubcategory && (
        <div className="selection-summary">
          <strong>Selected:</strong>
          <div>
            {selectedCategory} → {selectedSubcategory}
          </div>
          {currentClassification && currentClassification.source === 'ai_generated' && (
            <div className="ai-classification-note">
              <span className="ai-badge" title="AI-generated classification">AI Classification</span>
            </div>
          )}
          {currentClassification && currentClassification.source === 'uncategorized' && (
            <div className="ai-classification-note">
              <span className="uncategorized-badge" title="Not yet manually classified">Uncategorized</span>
            </div>
          )}
        </div>
      )}

      <div className="category-actions">
        <button
          type="button"
          onClick={() => setShowAddCategory(!showAddCategory)}
          className="btn btn-small"
        >
          + Add Category
        </button>
        <button
          type="button"
          onClick={() => setShowAddSubcategory(!showAddSubcategory)}
          className="btn btn-small"
          disabled={!selectedCategory}
          title={!selectedCategory ? "Select a category first" : "Add subcategory to selected category"}
        >
          + Add Subcategory
        </button>
      </div>

      {showAddCategory && (
        <div className="add-form">
          <input
            type="text"
            placeholder="Category name"
            value={newCategoryName}
            onChange={(e) => setNewCategoryName(e.target.value)}
          />
          <input
            type="text"
            placeholder="Description"
            value={newCategoryDesc}
            onChange={(e) => setNewCategoryDesc(e.target.value)}
          />
          <button type="button" onClick={handleAddCategory} className="btn btn-small">Add</button>
          <button
            type="button"
            onClick={() => setShowAddCategory(false)}
            className="btn btn-small"
          >
            Cancel
          </button>
        </div>
      )}

      {showAddSubcategory && (
        <div className="add-form">
          <div className="parent-category-selector">
            <label>Adding to:</label>
            <select 
              value={selectedCategory || ''} 
              onChange={(e) => onSelectCategory(e.target.value)}
              className="category-dropdown"
            >
              {Object.keys(categories.categories).map(catName => (
                <option key={catName} value={catName}>{catName}</option>
              ))}
            </select>
          </div>
          <input
            type="text"
            placeholder="Subcategory name"
            value={newSubcategoryName}
            onChange={(e) => setNewSubcategoryName(e.target.value)}
          />
          <input
            type="text"
            placeholder="Description"
            value={newSubcategoryDesc}
            onChange={(e) => setNewSubcategoryDesc(e.target.value)}
          />
          <button type="button" onClick={handleAddSubcategory} className="btn btn-small">Add</button>
          <button
            type="button"
            onClick={() => setShowAddSubcategory(false)}
            className="btn btn-small"
          >
            Cancel
          </button>
        </div>
      )}

      <div className="category-list">
        {Object.entries(categories.categories).map(([catName, catData]) => (
          <div key={catName} className="category-item">
            <div
              className={`category-name ${selectedCategory === catName ? 'selected' : ''}`}
              onClick={() => toggleCategory(catName)}
            >
              <span className="expand-icon">
                {expandedCategories[catName] ? '▼' : '▶'}
              </span>
              {catName}
            </div>

            {expandedCategories[catName] && catData.subcategories && (
              <div className="subcategory-list">
                {Object.entries(catData.subcategories).map(([subName, subData]) => (
                  <div
                    key={subName}
                    className={`subcategory-item ${
                      selectedCategory === catName && selectedSubcategory === subName
                        ? 'selected'
                        : ''
                    }`}
                    onClick={() => handleSelectSubcategory(catName, subName)}
                  >
                    <span className="radio-icon">
                      {selectedCategory === catName && selectedSubcategory === subName ? '●' : '○'}
                    </span>
                    {subName}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default CategoryTree;
