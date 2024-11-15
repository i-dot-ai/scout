import React from 'react';

const AuthError: React.FC = () => {
  return (
    <div className="auth-error-container">
      <div className="auth-error-content">
        <h2>Authentication Error</h2>
        <p>We could not authenticate your credentials. Please contact support.</p>
      </div>
    </div>
  );
};

export default AuthError;
