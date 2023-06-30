" Local .vimrc
" Vim will source these if `exrc` is configured in the default .vimrc file.
" Based on this guide:
" https://www.alexeyshmalko.com/2014/using-vim-as-c-cpp-ide/

set tabstop=4
set softtabstop=4
set shiftwidth=4
set noexpandtab

set colorcolumn=80
highlight ColorColumn ctermbg=darkgray

" parse compile_commands.json (should be in build/cmake-build and symlinked in
" project root)
let g:ale_c_parse_compile_commands=1
let g:ale_c_parse_makefile=1

let &path.=$IDF_PATH."/components/freertos/include,"
let &path.=$IDF_PATH."/components/esp_system/include,"
let &path.=$IDF_PATH."/components/esp_wifi/include,"
let &path.=$IDF_PATH."/components/esp_event/include,"
let &path.=$IDF_PATH."/components/esp_log/include,"
let &path.=$IDF_PATH."/components/driver/include,"
let &path.=$IDF_PATH."/components/esp_adc_cal/include,"
let &path.=$IDF_PATH."/components/lwip/include,"

let my_c_options='-I'.substitute(&path, ',', '\n-I', 'g')
let g:ale_c_cc_options='-std=c11 -Wall '.my_c_options

" Can't get rid of linter errors, so give up and disable all highlights:
let g:ale_set_highlights=0
