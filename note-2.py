import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup

class DatabaseManager:
    def __init__(self):
        # Connect to SQLite database (creates one if it doesn't exist)
        self.conn = sqlite3.connect('notes.db')
        self.cursor = self.conn.cursor()
        
        # Create notes table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def add_note(self, content):
        # Insert new note into the database
        self.cursor.execute('INSERT INTO notes (content) VALUES (?)', (content,))
        self.conn.commit()

    def get_all_notes(self):
        # Retrieve all notes ordered by latest first
        self.cursor.execute('SELECT id, content, created_at FROM notes ORDER BY created_at DESC')
        return self.cursor.fetchall()

    def update_note(self, note_id, new_content):
        # Update existing note content and timestamp
        self.cursor.execute('''
            UPDATE notes 
            SET content = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (new_content, note_id))
        self.conn.commit()

    def delete_note(self, note_id):
        # Delete note from database
        self.cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
        self.conn.commit()

class NoteWidget(BoxLayout):
    def __init__(self, note_id, content, created_at, notes_app, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.padding = 5
        self.spacing = 5
        self.note_id = note_id
        self.notes_app = notes_app

        # Create a label with note content and timestamp
        timestamp = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
        self.content = Label(
            text=f'{content}\n[size=12][color=808080]{timestamp}[/color][/size]',
            markup=True,
            size_hint_x=0.7,
            text_size=(None, None)
        )

        # Create edit and delete buttons
        edit_button = Button(
            text='Редактировать',
            size_hint_x=0.15
        )
        delete_button = Button(
            text='Удалить',
            size_hint_x=0.15
        )

        # Bind button actions
        edit_button.bind(on_press=self.edit_note)
        delete_button.bind(on_press=self.delete_note)

        # Add widgets to layout
        self.add_widget(self.content)
        self.add_widget(edit_button)
        self.add_widget(delete_button)

    def edit_note(self, instance):
        # Create popup for editing note
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Add text input with current note content
        self.edit_input = TextInput(
            text=self.content.text.split('\n')[0],  # Get only content, not timestamp
            multiline=True
        )
        
        # Add save button
        save_button = Button(
            text='Сохранить',
            size_hint_y=None,
            height=50
        )
        
        # Create and bind popup
        popup = Popup(
            title='Редактировать заметку',
            content=content,
            size_hint=(0.9, 0.9)
        )
        
        save_button.bind(on_press=lambda x: self.save_edited_note(popup))
        
        content.add_widget(self.edit_input)
        content.add_widget(save_button)
        popup.open()

    def save_edited_note(self, popup):
        # Update note in database and refresh display
        new_content = self.edit_input.text
        self.notes_app.db.update_note(self.note_id, new_content)
        self.notes_app.refresh_notes()
        popup.dismiss()

    def delete_note(self, instance):
        # Delete note from database and refresh display
        self.notes_app.db.delete_note(self.note_id)
        self.notes_app.refresh_notes()

class NotesApp(App):
    def build(self):
        # Initialize database
        self.db = DatabaseManager()
        
        # Create main layout
        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Add header
        header = Label(
            text='Мои заметки',
            size_hint_y=None,
            height=50,
            font_size='20sp'
        )
        
        # Create input area
        input_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=100,
            spacing=10
        )
        
        # Add note input
        self.note_input = TextInput(
            hint_text='Введите вашу заметку...',
            multiline=True,
            size_hint_x=0.8
        )
        
        # Add save button
        save_button = Button(
            text='Сохранить',
            size_hint_x=0.2
        )
        save_button.bind(on_press=self.save_note)
        
        # Add widgets to input layout
        input_layout.add_widget(self.note_input)
        input_layout.add_widget(save_button)
        
        # Create scrollable area for notes
        scroll_layout = ScrollView()
        self.notes_layout = GridLayout(
            cols=1,
            spacing=40,
            size_hint_y=None,
            padding=10
        )
        self.notes_layout.bind(minimum_height=self.notes_layout.setter('height'))
        
        # Add all layouts to main layout
        self.main_layout.add_widget(header)
        self.main_layout.add_widget(input_layout)
        
        # Add scrollview with notes
        scroll_layout.add_widget(self.notes_layout)
        self.main_layout.add_widget(scroll_layout)
        
        # Load existing notes
        self.refresh_notes()
        
        return self.main_layout

    def save_note(self, instance):
        # Save note to database
        note_text = self.note_input.text.strip()
        if note_text:
            self.db.add_note(note_text)
            self.note_input.text = ''  # Clear input
            self.refresh_notes()

    def refresh_notes(self):
        # Clear and reload all notes
        self.notes_layout.clear_widgets()
        notes = self.db.get_all_notes()
        
        for note in notes:
            note_widget = NoteWidget(
                note_id=note[0],
                content=note[1],
                created_at=note[2],
                notes_app=self
            )
            self.notes_layout.add_widget(note_widget)

if __name__ == '__main__':
    NotesApp().run()