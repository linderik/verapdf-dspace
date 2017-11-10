from oai import *
from f_filesys import *
from f_inet import *
from f_string import *
from f_xml import *
import xml.dom.minidom
import subprocess
import sys

stats = dict()
result = [0, 0]
url = 'http://doria.fi/oai/request' # The dspace to harvest. Modify as needed.
vera = '/home/merioksa/Software/verapdf/verapdf' # MODIFY THIS! Needs to point at the actual verapdf script


def get_file_list(id):
    kk = oai_GetRecord(url, id, 'kk')
    dom_kk = xml.dom.minidom.parseString(kk)

    return dom_kk.getElementsByTagName('kk:file')


def download_file(file_element):
    link = file_element.getAttribute('href')

    return get_url(str2url(link))


def check_pdf(pdf_file):
    # Runs vera to check the pdf file, then stores an xml file with the reults
    print("Running verapdf")
    output = subprocess.check_output(['sh', vera, pdf_file, '--format', 'xml', '--maxfailures', '3'])
    f = open("result.xml", "w")
    f.write(output)
    f.close()


def parse_result():
    # parses output xml from verapdf and stores error in result dictionary
    print("Parsing results...")
    xml_file = xml.dom.minidom.parse('result.xml')
    report_tag = xml_file.getElementsByTagName('validationReports')[0]
    if report_tag.getAttribute('compliant') == '1':
        print("Compliant File")
        return True
    elif report_tag.getAttribute('compliant') == '0' and report_tag.getAttribute('nonCompliant') == '1':
        print("Non Compliant File, Errors:")

        assertions = xml_file.getElementsByTagName('assertion')
        for assertion in assertions:
            msg = assertion.getElementsByTagName('message')[0].firstChild.nodeValue
            print "- " + msg


        return False
    else:
        print('Error: XML result tag not found!')
        sys.exit(1)


def store_result(passed):
    # Save result of latest check
    if passed:
        result[0] = result[0] + 1
    else:
        result[1] = result[1] + 1


def write_stats():
    print("Results:")
    res = 'Passed: ' + str(result[0]) + '; Failed: ' + str(result[1])
    print res
    open('result.txt', 'w').write(res)


def check_database():
    counter = 0

    # Download all identifiers from dspace
    items = oai_ListIdentifiers(url)  # The second (optional) argument is the collection or community id :-)
    for orig_id, orig_ts in items.iteritems():
        print("===================================================================")

        elems = get_file_list(orig_id)

        # Check that we have some files. If not, log error
        if len(elems) > 0:
            # Fetch the actual files (pdfs etc)
            for elem in elems:
                content = download_file(elem)

                if content is None:
                    # Something went wrong!!
                    print("Could not download all files" + orig_id)
                else:
                    write_file(content, 'temp.pdf')

                    # Super simple file type check. Is this enough?
                    filetype = subprocess.check_output(['file', 'temp.pdf'])
                    if 'PDF' in filetype:
                        check_pdf('temp.pdf')
                        store_result(parse_result())
                    else:
                        print("That's not a PDF!")
        else:
            print("No files found!")

        counter += 1
        if counter == 50:
            print("Max number of iterations reached!")
            break

    print("===================================================================")
    write_stats()


if __name__ == "__main__":
    check_database()
