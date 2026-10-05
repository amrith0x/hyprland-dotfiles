function firefox --wraps='flatpak run org.mozilla.firefox' --description 'alias firefox=flatpak run org.mozilla.firefox'
    flatpak run org.mozilla.firefox $argv
end
