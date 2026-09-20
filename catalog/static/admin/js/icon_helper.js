/**
 * LuxWood Admin - Icon Helper
 * Помощник для выбора иконок Font Awesome
 */

(function() {
    'use strict';
    
    document.addEventListener('DOMContentLoaded', function() {
        const iconItems = document.querySelectorAll('.icon-helper-item');
        const iconInput = document.getElementById('id_icon');
        
        if (!iconInput || iconItems.length === 0) {
            return;
        }
        
        // Обработчик клика на иконку
        iconItems.forEach(function(item) {
            item.addEventListener('click', function() {
                const iconClass = this.getAttribute('data-icon');
                if (iconClass && iconInput) {
                    iconInput.value = iconClass;
                    
                    // Визуальная обратная связь
                    iconInput.style.borderColor = '#4caf50';
                    iconInput.style.boxShadow = '0 0 0 2px rgba(76, 175, 80, 0.2)';
                    
                    setTimeout(function() {
                        iconInput.style.borderColor = '';
                        iconInput.style.boxShadow = '';
                    }, 1000);
                    
                    // Показываем превью выбранной иконки
                    showIconPreview(iconClass);
                }
            });
        });
        
        // Показываем превью при вводе вручную
        if (iconInput) {
            iconInput.addEventListener('input', function() {
                const value = this.value.trim();
                if (value) {
                    showIconPreview(value);
                } else {
                    hideIconPreview();
                }
            });
            
            // Показываем превью текущего значения при загрузке
            if (iconInput.value) {
                showIconPreview(iconInput.value);
            }
        }
    });
    
    function showIconPreview(iconClass) {
        let preview = document.getElementById('icon-preview');
        
        if (!preview) {
            preview = document.createElement('div');
            preview.id = 'icon-preview';
            preview.className = 'icon-preview';
            preview.innerHTML = '<span class="icon-preview-label">Превью:</span><i class="' + iconClass + '"></i>';
            
            const iconInput = document.getElementById('id_icon');
            if (iconInput && iconInput.parentNode) {
                iconInput.parentNode.appendChild(preview);
            }
        } else {
            const icon = preview.querySelector('i');
            if (icon) {
                icon.className = iconClass;
            }
        }
        
        preview.style.display = 'flex';
    }
    
    function hideIconPreview() {
        const preview = document.getElementById('icon-preview');
        if (preview) {
            preview.style.display = 'none';
        }
    }
})();


