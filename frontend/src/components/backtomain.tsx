import React from 'react'

export default function Backtomain() {
  return (
             <a
                    href="/"
                    className="flex items-center text-cyan-400 hover:text-cyan-300 transition mr-4 group"
                  >
                    <span className="flex items-center justify-center w-9 h-9 rounded-full bg-gray-800 border border-cyan-400 group-hover:scale-110 transition-transform duration-200">
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M15 19l-7-7 7-7"
                        />
                      </svg>
                    </span>
                  </a>
  )
}

