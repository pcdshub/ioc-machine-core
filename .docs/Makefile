all: script_order.png

%.png: %.dot
	sfdp -Tpng $< > $@

clean:
	rm -f *.png
