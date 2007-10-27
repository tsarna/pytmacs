# The literary works of Etaoin Shrdlu

"""Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do
eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip
ex ea commodo consequat. Duis aute irure dolor in reprehenderit in
voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur
sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt
mollit anim id est laborum."""

# This is some of the rest of the text that Lorem Ipsum was taken from.
# We don't generate this, but use it to enrich the probabilities table.

_more = """Sed ut perspiciatis, unde omnis iste natus error sit
voluptatem accusantium doloremque laudantium, totam rem aperiam eaque
ipsa, quae ab illo inventore veritatis et quasi architecto beatae vitae
dicta sunt, explicabo. Nemo enim ipsam voluptatem, quia voluptas sit,
aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos,
qui ratione voluptatem sequi nesciunt, neque porro quisquam est, qui
doquia quia non numquam quaerat voluptatem. emporis suscipit, vel eum
qui ea, quam nihil molestiae consequatur, vel, qui, quo voluptas? At
vero eos et accusamus et iusto odio dignissimos ducimus, qui blanditiis
praesentium voluptatum deleniti atque corrupti, quos dolores et quas
molestias, similique et dolorum fuga. Et harum quidem rerum facilis est
et expedita distinctio. Nam libero tempore, cum soluta nobis est
eligendi optio, cumque nihil impedit, quo minus id, quod maxime placeat,
facere possimus, omnis voluptas assumenda est, omnis dolor repellendus.
Temporibus autem quibusdam et aut officiis debitis aut rerum
necessitatibus saepe eveniet, ut et voluptates repudiandae sint et
molestiae non recusandae. Itaque earum rerum hic tenetur a sapiente
delectus, ut aut reiciendis voluptatibus maiores alias consequatur aut
perferendis doloribus asperiores repellat."""


from random import choice

# build probabilities data

def _mkprobs(s, probs, starts):
    f = s[0].lower()
    starts.append(f)
    probs = {}

    last = ' '  + f
    for c in s[1:] + ' ':
        if c == '\n':
            c = ' '
        else:
            c = c.lower()
        probs[last] = probs.get(last, "") + c.lower()
        if last[1] == ' ':
            starts.append(c)
        last = last[1]+c

    return probs, starts


_probs, _starts = _mkprobs(__doc__, {}, [])
_defaultnwords = len(_starts)
_probs, _starts = _mkprobs(_more, _probs, _starts)
    

def genword():
    l = [choice(_starts)]
    last = ' '+l[0]
    while True:
        # as words get longer, stack the odds of ending
        tries = max((len(l) - 7) // 5, 0) + 1
        for x in range(tries):
            c = choice(_probs[last])
            if c == ' ':
                return ''.join(l)

        if len(l) > 12:
            c = choice(_probs[last])
            if c == ' ':
                return ''.join(l)
        l.append(c)
        last = last[1] + c


def loremwords():
    l = __doc__.split()
    for w in l:
        yield w

    start = True

    last = None
    while True:
        w = genword()
        if w == last:
            continue

        last = w            
        if start:
            w = w.title()
        start = (w[-1] in '.?')

        yield w


class WordUnicodeFile(object):
    def __init__(self):
        self.left = 0
        self.buf = []
        self.gen = loremwords()

    def reset(self):
        self.gen = loremwords()

    def want(self, n=True):
        """
        If n is True, EOF will be after one sentence.
        else EOF will be after n words.
        """
        
        self.left = n
        
    def read(self, n):
        if n != 1:
            raise ValueError, \
                "This cheezy file-like only supports reading one char at a time"
            
        if not self.buf and self.left:
            w = self.gen.next()
            self.buf = [unicode(c) for c in w]
            if self.left is True:
                if self.buf[-1] in u'.?':
                    self.left = 0 # Force EOF at end of sentence 
            else:
                self.left -= 1
            self.buf.append(u' ')

        if self.buf:
            return self.buf.pop(0)
        else:
            return u""


_wf = WordUnicodeFile()


from tmacs.app.commands import *
import __tmacs__

@command
@annotate(UniArg)
def ipsum(n=True):
    if not n:
        # reset generator
        _wf.reset()
        return
        
    _wf.want(n)
    __tmacs__.ui.pushplayback(_wf)
