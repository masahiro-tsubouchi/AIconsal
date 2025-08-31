/**
 * Input Component
 * Manufacturing AI Assistant Frontend
 */

import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  className = '',
  ...props
}) => {
  const inputClasses = `
    block w-full px-3 py-2 border rounded-md shadow-sm text-sm
    focus:ring-2 focus:ring-offset-0 focus:outline-none
    disabled:opacity-50 disabled:cursor-not-allowed
    ${error
      ? 'border-error-300 focus:border-error-500 focus:ring-error-200'
      : 'border-secondary-300 focus:border-primary-500 focus:ring-primary-200'
    }
    ${className}
  `;

  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-sm font-medium text-secondary-700">
          {label}
        </label>
      )}
      <input className={inputClasses} {...props} />
      {error && (
        <p className="text-sm text-error-600">{error}</p>
      )}
      {helperText && !error && (
        <p className="text-sm text-secondary-500">{helperText}</p>
      )}
    </div>
  );
};

export default Input;
