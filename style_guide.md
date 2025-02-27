# Audio to Mic Player Style Guide

This document outlines the styling guidelines for the Audio to Mic Player application.

## Layout

The application has a fixed window size of 780x580 pixels to ensure consistent UI rendering. The main layout consists of:

1. **Header Bar** - Contains logo, app title and theme selector
2. **Left Sidebar** - Contains device selection, voice mode settings and volume control
3. **Main Content Area** - Contains the list of audio files
4. **Player Bar** - Fixed at the bottom of the window, contains playback controls and progress bar

## Color Themes

The application supports multiple color themes, each with a consistent color palette:

### Dark Blue (Default)
- Primary Background: `#1a1a2e`
- Secondary Background: `#252538`
- Tertiary Background: `#1e1e30`
- Primary Accent: `#4cc9f0`
- Secondary Accent: `#f72585`
- Button Background: `#3a3a5e`
- Button Hover: `#4a4a6e`
- Primary Text: `#edf2f4`
- Secondary Text: `#8d99ae`

### Dark Purple
- Primary Background: `#240046`
- Secondary Background: `#3c096c`
- Tertiary Background: `#2d0049`
- Primary Accent: `#7b2cbf`
- Secondary Accent: `#ff9e00`
- Button Background: `#5a189a`
- Button Hover: `#7b2cbf`
- Primary Text: `#edf2f4`
- Secondary Text: `#c8b6ff`

### Dark Green
- Primary Background: `#1a281f`
- Secondary Background: `#2a403a`
- Tertiary Background: `#1f3329`
- Primary Accent: `#2d6a4f`
- Secondary Accent: `#d8f3dc`
- Button Background: `#40916c`
- Button Hover: `#52b788`
- Primary Text: `#edf2f4`
- Secondary Text: `#b7e4c7`

## Typography

Text elements follow a consistent hierarchy:

- **App Title**: Bold, 18px
- **Section Headers**: Bold, 12px, uppercase
- **Regular Text**: Normal, 12px
- **Small Text**: Normal, 10px

## Components

### Buttons
- Standard buttons: Height 28px, corner radius 6px
- Circular buttons: Height 30px, corner radius 15px
- Main action button (Play/Pause): Accent color

### Progress Bar
- Height: 16px
- Handle size: 16px
- Shows track position with time indicators on both sides

### Input Fields
- Search field: Height 28px, light border

## Layout Preview

![Layout Preview](layout_preview.png)

*This preview shows the general layout of the application with fixed dimensions.*
