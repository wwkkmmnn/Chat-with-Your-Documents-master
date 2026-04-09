import React, { useState } from 'react';
import styled from 'styled-components';
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  min-height: 100vh;
  background-color: #f7f7f7;
  font-family: 'Inter', sans-serif;
`;

const Title = styled.h1`
  margin-bottom: 20px;
  color: #333;
  font-size: 24px;
  font-weight: 600;
`;

const App = () => {
  const [uploadedFile, setUploadedFile] = useState(null);

  return (
    <AppContainer>
      <Title>Chat with Your Documents</Title>
      <FileUpload onFileUpload={setUploadedFile} currentFile={uploadedFile} />
      <ChatInterface documentName={uploadedFile?.name} />
    </AppContainer>
  );
};

export default App;