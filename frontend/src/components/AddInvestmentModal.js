import React, { useState } from 'react';
import { X } from 'lucide-react';

const AddInvestmentModal = ({ isOpen, onClose, onAdd }) => {
  const [formData, setFormData] = useState({
    security: '',
    platform: '',
    quantity: '',
    price: '',
    date: new Date().toISOString().split('T')[0],
    fees: '0',
  });

  const [errors, setErrors] = useState({});

  const platforms = [
    'Interactive Brokers',
    'Trading 212',
    'Freetrade',
    'eToro',
    'Hargreaves Lansdown',
    'AJ Bell',
  ];

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.security.trim()) newErrors.security = 'Security is required';
    if (!formData.platform) newErrors.platform = 'Platform is required';
    if (!formData.quantity || parseFloat(formData.quantity) <= 0) {
      newErrors.quantity = 'Quantity must be greater than 0';
    }
    if (!formData.price || parseFloat(formData.price) <= 0) {
      newErrors.price = 'Price must be greater than 0';
    }
    if (!formData.date) newErrors.date = 'Date is required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      const investment = {
        ...formData,
        quantity: parseFloat(formData.quantity),
        price: parseFloat(formData.price),
        fees: parseFloat(formData.fees),
        totalValue: parseFloat(formData.quantity) * parseFloat(formData.price),
      };
      onAdd(investment);
      setFormData({
        security: '',
        platform: '',
        quantity: '',
        price: '',
        date: new Date().toISOString().split('T')[0],
        fees: '0',
      });
      onClose();
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Add New Investment</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Security Symbol
            </label>
            <input
              type="text"
              name="security"
              value={formData.security}
              onChange={handleChange}
              placeholder="e.g., AAPL, GOOGL"
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.security ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.security && (
              <p className="text-red-500 text-xs mt-1">{errors.security}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Platform
            </label>
            <select
              name="platform"
              value={formData.platform}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.platform ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">Select platform</option>
              {platforms.map(platform => (
                <option key={platform} value={platform}>{platform}</option>
              ))}
            </select>
            {errors.platform && (
              <p className="text-red-500 text-xs mt-1">{errors.platform}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Quantity
              </label>
              <input
                type="number"
                name="quantity"
                value={formData.quantity}
                onChange={handleChange}
                step="0.000001"
                min="0"
                placeholder="0"
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.quantity ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.quantity && (
                <p className="text-red-500 text-xs mt-1">{errors.quantity}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Price per Share
              </label>
              <input
                type="number"
                name="price"
                value={formData.price}
                onChange={handleChange}
                step="0.01"
                min="0"
                placeholder="0.00"
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.price ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.price && (
                <p className="text-red-500 text-xs mt-1">{errors.price}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Purchase Date
            </label>
            <input
              type="date"
              name="date"
              value={formData.date}
              onChange={handleChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.date ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.date && (
              <p className="text-red-500 text-xs mt-1">{errors.date}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Trading Fees (optional)
            </label>
            <input
              type="number"
              name="fees"
              value={formData.fees}
              onChange={handleChange}
              step="0.01"
              min="0"
              placeholder="0.00"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {formData.quantity && formData.price && (
            <div className="bg-gray-50 p-3 rounded-md">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total Investment:</span>
                <span className="font-medium">
                  £{(parseFloat(formData.quantity || 0) * parseFloat(formData.price || 0)).toFixed(2)}
                </span>
              </div>
              {parseFloat(formData.fees || 0) > 0 && (
                <div className="flex justify-between text-sm mt-1">
                  <span className="text-gray-600">Trading Fees:</span>
                  <span className="font-medium">£{parseFloat(formData.fees).toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between text-sm mt-1 pt-1 border-t border-gray-200">
                <span className="text-gray-900 font-medium">Total Cost:</span>
                <span className="font-bold">
                  £{(parseFloat(formData.quantity || 0) * parseFloat(formData.price || 0) + parseFloat(formData.fees || 0)).toFixed(2)}
                </span>
              </div>
            </div>
          )}

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Add Investment
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddInvestmentModal;