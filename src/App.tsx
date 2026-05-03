import React from 'react';
import { Sidebar } from './components/Sidebar';
import { SearchBar } from './components/SearchBar';
import { Feed } from './components/Feed';
import { useFeed } from './hooks/useFeed';

function App() {
  useFeed();

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-gray-100 overflow-hidden text-[15px] italic" style={{ fontFamily: 'Times New Roman' }}>
      <Sidebar />
      <main className="flex-1 flex flex-col h-full overflow-y-auto relative">
        <Feed />
      </main>
    </div>
  );
}

export default App;
