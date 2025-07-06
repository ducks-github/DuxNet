"""
Service Detail View for DuxOS Desktop

Provides detailed service information, install/invoke functionality, and review/rating features.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QSpinBox, QLineEdit, QScrollArea, QFrame, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class ServiceDetailView(QWidget):
    install_requested = pyqtSignal(str)  # service_id
    invoke_requested = pyqtSignal(str)   # service_id
    review_submitted = pyqtSignal(str, int, str, str)  # service_id, rating, title, content
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.current_service = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Service info section
        self.service_info = QLabel("Select a service to view details")
        self.service_info.setWordWrap(True)
        self.service_info.setFont(QFont("Arial", 12))
        layout.addWidget(self.service_info)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.install_button = QPushButton("Install")
        self.install_button.clicked.connect(self.install_service)
        self.invoke_button = QPushButton("Invoke API")
        self.invoke_button.clicked.connect(self.invoke_service)
        self.favorite_button = QPushButton("Add to Favorites")
        self.favorite_button.clicked.connect(self.toggle_favorite)
        
        button_layout.addWidget(self.install_button)
        button_layout.addWidget(self.invoke_button)
        button_layout.addWidget(self.favorite_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Tab widget for details, reviews, etc.
        self.tab_widget = QTabWidget()
        
        # Details tab
        self.details_tab = QWidget()
        self.setup_details_tab()
        self.tab_widget.addTab(self.details_tab, "Details")
        
        # Reviews tab
        self.reviews_tab = QWidget()
        self.setup_reviews_tab()
        self.tab_widget.addTab(self.reviews_tab, "Reviews")
        
        # Add review tab
        self.add_review_tab = QWidget()
        self.setup_add_review_tab()
        self.tab_widget.addTab(self.add_review_tab, "Add Review")
        
        layout.addWidget(self.tab_widget)
        
        # Initially disable buttons
        self.install_button.setEnabled(False)
        self.invoke_button.setEnabled(False)
        self.favorite_button.setEnabled(False)
    
    def setup_details_tab(self):
        layout = QVBoxLayout(self.details_tab)
        
        # Scrollable area for details
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Service details labels
        self.detail_labels = {}
        detail_fields = [
            "category", "version", "owner_name", "price_per_call", "price_currency",
            "free_tier_calls", "rate_limit_per_hour", "total_calls", "total_revenue",
            "rating_count", "average_rating", "status", "created_at", "updated_at"
        ]
        
        for field in detail_fields:
            label = QLabel(f"{field.replace('_', ' ').title()}: ")
            label.setFont(QFont("Arial", 10, QFont.Bold))
            value = QLabel("")
            value.setWordWrap(True)
            
            field_layout = QHBoxLayout()
            field_layout.addWidget(label)
            field_layout.addWidget(value)
            field_layout.addStretch()
            details_layout.addLayout(field_layout)
            
            self.detail_labels[field] = value
        
        # Tags section
        tags_label = QLabel("Tags:")
        tags_label.setFont(QFont("Arial", 10, QFont.Bold))
        details_layout.addWidget(tags_label)
        
        self.tags_label = QLabel("")
        self.tags_label.setWordWrap(True)
        details_layout.addWidget(self.tags_label)
        
        # Documentation links
        doc_label = QLabel("Documentation:")
        doc_label.setFont(QFont("Arial", 10, QFont.Bold))
        details_layout.addWidget(doc_label)
        
        self.doc_label = QLabel("")
        self.doc_label.setWordWrap(True)
        details_layout.addWidget(self.doc_label)
        
        details_layout.addStretch()
        scroll.setWidget(details_widget)
        layout.addWidget(scroll)
    
    def setup_reviews_tab(self):
        layout = QVBoxLayout(self.reviews_tab)
        
        # Reviews list
        self.reviews_list = QTextEdit()
        self.reviews_list.setReadOnly(True)
        layout.addWidget(self.reviews_list)
    
    def setup_add_review_tab(self):
        layout = QVBoxLayout(self.add_review_tab)
        
        # Rating
        rating_layout = QHBoxLayout()
        rating_layout.addWidget(QLabel("Rating:"))
        self.rating_spinbox = QSpinBox()
        self.rating_spinbox.setRange(1, 5)
        self.rating_spinbox.setValue(5)
        rating_layout.addWidget(self.rating_spinbox)
        rating_layout.addStretch()
        layout.addLayout(rating_layout)
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.review_title = QLineEdit()
        self.review_title.setPlaceholderText("Enter review title...")
        title_layout.addWidget(self.review_title)
        layout.addLayout(title_layout)
        
        # Content
        layout.addWidget(QLabel("Review:"))
        self.review_content = QTextEdit()
        self.review_content.setPlaceholderText("Enter your review...")
        self.review_content.setMaximumHeight(100)
        layout.addWidget(self.review_content)
        
        # Submit button
        self.submit_review_button = QPushButton("Submit Review")
        self.submit_review_button.clicked.connect(self.submit_review)
        layout.addWidget(self.submit_review_button)
        
        layout.addStretch()
    
    def show_service(self, service_data):
        """Display service details"""
        self.current_service = service_data
        
        # Update service info
        info_text = f"<h2>{service_data['name']}</h2>"
        info_text += f"<p><b>Description:</b> {service_data['description']}</p>"
        self.service_info.setText(info_text)
        
        # Update detail labels
        for field, label in self.detail_labels.items():
            value = service_data.get(field, "N/A")
            if isinstance(value, float):
                value = f"{value:.2f}"
            label.setText(str(value))
        
        # Update tags
        tags = ", ".join(service_data.get("tags", []))
        self.tags_label.setText(tags)
        
        # Update documentation
        doc_url = service_data.get("documentation_url")
        if doc_url:
            self.doc_label.setText(f"<a href='{doc_url}'>{doc_url}</a>")
        else:
            self.doc_label.setText("No documentation available")
        
        # Enable buttons
        self.install_button.setEnabled(True)
        self.invoke_button.setEnabled(True)
        self.favorite_button.setEnabled(True)
        
        # Load reviews
        self.load_reviews()
    
    def load_reviews(self):
        """Load and display reviews for the current service"""
        if not self.current_service:
            return
        
        try:
            reviews = self.api_client.get_service_reviews(self.current_service["service_id"])
            
            reviews_text = ""
            for review in reviews:
                stars = "★" * review["rating"] + "☆" * (5 - review["rating"])
                reviews_text += f"<h4>{review['title']} {stars}</h4>"
                reviews_text += f"<p><b>By:</b> {review['user_name']} on {review['created_at']}</p>"
                reviews_text += f"<p>{review['content']}</p>"
                reviews_text += "<hr>"
            
            if not reviews:
                reviews_text = "No reviews yet. Be the first to review this service!"
            
            self.reviews_list.setHtml(reviews_text)
            
        except Exception as e:
            self.reviews_list.setPlainText(f"Error loading reviews: {e}")
    
    def install_service(self):
        """Request service installation"""
        if self.current_service:
            self.install_requested.emit(self.current_service["service_id"])
    
    def invoke_service(self):
        """Request service invocation"""
        if self.current_service:
            self.invoke_requested.emit(self.current_service["service_id"])
    
    def toggle_favorite(self):
        """Toggle favorite status"""
        if self.current_service:
            # This would need user_id from the main app
            # For now, just show a message
            self.favorite_button.setText("Added to Favorites" if self.favorite_button.text() == "Add to Favorites" else "Add to Favorites")
    
    def submit_review(self):
        """Submit a new review"""
        if not self.current_service:
            return
        
        rating = self.rating_spinbox.value()
        title = self.review_title.text().strip()
        content = self.review_content.toPlainText().strip()
        
        if not title or not content:
            return  # Should show error message
        
        # This would need user_id and user_name from the main app
        # For now, use placeholder values
        user_id = "desktop_user"
        user_name = "Desktop User"
        
        try:
            self.api_client.add_review(
                self.current_service["service_id"],
                user_id, user_name, rating, title, content
            )
            
            # Clear form
            self.review_title.clear()
            self.review_content.clear()
            self.rating_spinbox.setValue(5)
            
            # Reload reviews
            self.load_reviews()
            
        except Exception as e:
            # Should show error message
            print(f"Error submitting review: {e}") 