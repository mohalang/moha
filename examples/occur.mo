def occur(term, sentence){
    occurs = [];
    if (term.length() == 0 || sentence.length() == 0 || term.length() > sentence.length()) {
        return occurs;
    }
    (term.length() <= sentence.length()) {
        i_sentence = 0;
        i_term = 0;
        i_last_term_char = term.length() - 1;
        i_last_sentence_char = sentence.length() - 1;
        do (i_sentence <= i_last_sentence_char && i_term <= i_last_term_char) {
            b_char_eq = sentence.index(i_sentence) == term.index(i_term);
            if (b_char_eq) {
                if (i_term == i_last_term_char) {
                    i_sentence = i_sentence - i_term;
                    occurs.push(i_sentence);
                    i_sentence = i_sentence + 1;
                    i_term = 0;
                } (i_term != i_last_term_char) {
                    i_term = i_term + 1;
                    i_sentence = i_sentence + 1;
                }
            } (!b_char_eq) {
                i_sentence = i_sentence + 1;
                i_term = 0;
            }
        }
        return occurs;
    }
}
print(occur("aba", "ababa"));
